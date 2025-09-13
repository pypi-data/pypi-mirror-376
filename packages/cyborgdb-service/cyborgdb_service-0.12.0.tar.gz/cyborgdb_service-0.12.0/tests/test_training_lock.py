"""
Test the cross-process training lock mechanism.
"""
import os
import time
import multiprocessing
from pathlib import Path
import tempfile
import pytest

from cyborgdb_service.core.training_lock import TrainingLock


def worker_acquire_lock(lock_dir: str, index_name: str, duration: float, result_queue):
    """Worker function to acquire a training lock."""
    try:
        lock = TrainingLock(lock_dir)
        
        # Try to acquire the lock
        with lock.acquire_training_lock(index_name, timeout=1.0):
            result_queue.put(("acquired", os.getpid(), time.time()))
            time.sleep(duration)
            result_queue.put(("released", os.getpid(), time.time()))
            
    except TimeoutError:
        result_queue.put(("timeout", os.getpid(), time.time()))
    except Exception as e:
        result_queue.put(("error", str(e), time.time()))


class TestTrainingLock:
    """Test the TrainingLock functionality."""
    
    def test_single_process_lock(self):
        """Test that a single process can acquire and release a lock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = TrainingLock(tmpdir)
            
            # Should be able to acquire lock
            with lock.acquire_training_lock("test_index", timeout=1.0):
                assert lock.is_training_locked()
                
                # Check training info
                info = lock.get_training_info()
                assert info is not None
                assert info["index_name"] == "test_index"
                assert info["pid"] == os.getpid()
            
            # Lock should be released
            assert not lock.is_training_locked()
    
    def test_multiple_process_exclusion(self):
        """Test that multiple processes cannot acquire the same lock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result_queue = multiprocessing.Queue()
            
            # Start first process that holds lock for 2 seconds
            p1 = multiprocessing.Process(
                target=worker_acquire_lock,
                args=(tmpdir, "test_index", 2.0, result_queue)
            )
            
            # Start second process that tries to acquire lock
            p2 = multiprocessing.Process(
                target=worker_acquire_lock,
                args=(tmpdir, "test_index", 0.5, result_queue)
            )
            
            p1.start()
            time.sleep(0.5)  # Let first process acquire lock
            p2.start()
            
            p1.join()
            p2.join()
            
            # Collect results
            results = []
            while not result_queue.empty():
                results.append(result_queue.get())
            
            # Verify results
            assert len(results) >= 3  # At least 3 events
            
            # First process should acquire and release
            p1_events = [r for r in results if len(r) > 1 and r[1] == p1.pid]
            assert any(r[0] == "acquired" for r in p1_events)
            assert any(r[0] == "released" for r in p1_events)
            
            # Second process should timeout
            p2_events = [r for r in results if len(r) > 1 and r[1] == p2.pid]
            assert any(r[0] == "timeout" for r in p2_events)
    
    def test_lock_cleanup(self):
        """Test that stale locks can be cleaned up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = TrainingLock(tmpdir)
            
            # Create a fake stale lock file
            stale_lock = lock.index_locks_dir / "stale_index.lock"
            stale_lock.write_text('{"pid": 99999, "index_name": "stale"}')
            
            # Create a recent lock file
            recent_lock = lock.index_locks_dir / "recent_index.lock"
            recent_lock.write_text('{"pid": 88888, "index_name": "recent"}')
            
            # Make stale lock old
            old_time = time.time() - 7200  # 2 hours ago
            os.utime(stale_lock, (old_time, old_time))
            
            # Clean up stale locks
            lock.cleanup_stale_locks(max_age_seconds=3600)
            
            # Stale lock should be removed
            assert not stale_lock.exists()
            
            # Recent lock should still exist
            assert recent_lock.exists()
    
    def test_lock_info_retrieval(self):
        """Test retrieving information about locks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = TrainingLock(tmpdir)
            
            # No lock initially
            assert not lock.is_training_locked()
            assert lock.get_training_info() is None
            
            # With lock
            with lock.acquire_training_lock("test_index", timeout=1.0):
                assert lock.is_training_locked()
                
                info = lock.get_training_info()
                assert info is not None
                assert info["index_name"] == "test_index"
                assert info["pid"] == os.getpid()
                
                # Check index-specific history
                history = lock.get_index_training_history("test_index")
                assert history is not None
                assert history["index_name"] == "test_index"
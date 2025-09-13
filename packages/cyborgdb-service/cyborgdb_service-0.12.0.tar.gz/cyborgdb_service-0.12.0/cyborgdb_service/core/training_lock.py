"""
Cross-process training lock manager using file-based locking.

This module provides a file-based locking mechanism to ensure only one
training operation can occur at a time across all worker processes.
"""
import os
import time
import json
import fcntl
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TrainingLock:
    """Manages cross-process training locks using file-based locking."""
    
    def __init__(self, lock_dir: str = "/tmp/cyborgdb_locks"):
        """
        Initialize the training lock manager.
        
        Args:
            lock_dir: Directory to store lock files
        """
        self.lock_dir = Path(lock_dir)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.global_lock_file = self.lock_dir / "training.lock"
        self.index_locks_dir = self.lock_dir / "indexes"
        self.index_locks_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TrainingLock initialized with lock directory: {self.lock_dir}")
    
    @contextmanager
    def acquire_training_lock(self, index_name: str, timeout: float = 5.0):
        """
        Acquire a global training lock for the specified index.
        
        This ensures only one training operation happens at a time across
        all worker processes.
        
        Args:
            index_name: Name of the index to train
            timeout: Maximum time to wait for lock (seconds)
            
        Yields:
            None if lock acquired successfully
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        lock_file = None
        index_lock_path = self.index_locks_dir / f"{index_name}.lock"
        
        try:
            # First, try to acquire a lock on the global training lock file
            lock_file = open(self.global_lock_file, 'w')
            start_time = time.time()
            
            while True:
                try:
                    # Try to acquire an exclusive lock (non-blocking)
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    
                    # Write lock info
                    lock_info = {
                        "pid": os.getpid(),
                        "index_name": index_name,
                        "timestamp": time.time(),
                        "worker_id": os.environ.get("APP_WORKER_ID", "unknown")
                    }
                    lock_file.write(json.dumps(lock_info))
                    lock_file.flush()
                    
                    # Also create an index-specific lock file for tracking
                    with open(index_lock_path, 'w') as idx_lock:
                        idx_lock.write(json.dumps(lock_info))
                    
                    logger.info(f"Process {os.getpid()} acquired training lock for index '{index_name}'")
                    break
                    
                except IOError:
                    # Lock is held by another process
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Could not acquire training lock for index '{index_name}' within {timeout} seconds")
                    
                    # Wait a bit before retrying
                    time.sleep(0.1)
            
            # Lock acquired, yield control
            yield
            
        finally:
            # Release the lock
            if lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                except Exception as e:
                    logger.error(f"Error releasing lock: {e}")
                    
            # Clean up index-specific lock file
            try:
                if index_lock_path.exists():
                    index_lock_path.unlink()
            except Exception as e:
                logger.error(f"Error removing index lock file: {e}")
                
    
    def is_training_locked(self) -> bool:
        """
        Check if any training is currently in progress.
        
        Returns:
            True if training lock is held, False otherwise
        """
        if not self.global_lock_file.exists():
            return False
            
        try:
            with open(self.global_lock_file, 'r') as lock_file:
                # Try to acquire a shared lock (non-blocking)
                # If we can't, someone has an exclusive lock
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    return False
                except IOError:
                    return True
        except Exception:
            return False
    
    def get_training_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current training operation if any.
        
        Returns:
            Dictionary with training info or None if no training in progress
        """
        if not self.is_training_locked():
            return None
            
        try:
            with open(self.global_lock_file, 'r') as lock_file:
                content = lock_file.read()
                if content:
                    return json.loads(content)
        except Exception as e:
            logger.error(f"Error reading training info: {e}")
            
        return None
    
    def get_index_training_history(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the last training info for a specific index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Dictionary with last training info or None
        """
        index_lock_path = self.index_locks_dir / f"{index_name}.lock"
        
        if not index_lock_path.exists():
            return None
            
        try:
            with open(index_lock_path, 'r') as f:
                return json.loads(f.read())
        except Exception as e:
            logger.error(f"Error reading index training history: {e}")
            return None
    
    def cleanup_stale_locks(self, max_age_seconds: float = 3600):
        """
        Clean up stale lock files older than max_age_seconds.
        
        Args:
            max_age_seconds: Maximum age of lock files in seconds
        """
        current_time = time.time()
        
        # Clean up index lock files
        for lock_file in self.index_locks_dir.glob("*.lock"):
            try:
                stat = lock_file.stat()
                if current_time - stat.st_mtime > max_age_seconds:
                    lock_file.unlink()
                    logger.info(f"Removed stale lock file: {lock_file}")
            except Exception as e:
                logger.error(f"Error cleaning up lock file {lock_file}: {e}")
        
        # Check global lock file
        if self.global_lock_file.exists():
            try:
                stat = self.global_lock_file.stat()
                if current_time - stat.st_mtime > max_age_seconds:
                    # Try to acquire lock before deleting
                    with open(self.global_lock_file, 'r') as f:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                            self.global_lock_file.unlink()
                            logger.info("Removed stale global training lock")
                        except IOError:
                            # Lock is active, don't delete
                            pass
            except Exception as e:
                logger.error(f"Error checking global lock file: {e}")
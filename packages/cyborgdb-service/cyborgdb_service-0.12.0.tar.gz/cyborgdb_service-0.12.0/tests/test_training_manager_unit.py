"""
Unit tests for TrainingManager that don't require cyborgdb_core.

These tests focus on the logic without requiring the actual CyborgDB modules.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Mock the cyborgdb modules before importing
sys.modules['cyborgdb_core'] = MagicMock()
sys.modules['cyborgdb_lite'] = MagicMock()


class TestTrainingManagerLogic:
    """Test the TrainingManager logic without actual CyborgDB dependencies."""
    
    def test_should_retrain_logic(self):
        """Test the retraining threshold logic."""
        # Import after mocking
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            manager._retrain_threshold = 10000
            
            # Test untrained index (effective n_lists = 1)
            # Threshold = 1 * 10000 = 10000
            assert manager.should_retrain("test_index", 9999, 128, False, "ivfflat") == False
            assert manager.should_retrain("test_index", 10001, 128, False, "ivfflat") == True
            assert manager.should_retrain("test_index", 20000, 128, False, "ivfflat") == True
            
            # Test trained index with n_lists=128
            # Threshold = 128 * 10000 = 1,280,000
            assert manager.should_retrain("test_index", 1_000_000, 128, True, "ivfflat") == False
            assert manager.should_retrain("test_index", 1_280_001, 128, True, "ivfflat") == True
            assert manager.should_retrain("test_index", 2_000_000, 128, True, "ivfflat") == True
    
    def test_should_retrain_various_n_lists(self):
        """Test retraining logic with various n_lists values."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            manager._retrain_threshold = 10000
            
            # n_lists = 64, trained
            # Threshold = 64 * 10000 = 640,000
            assert manager.should_retrain("test_index", 639_999, 64, True, "ivfflat") == False
            assert manager.should_retrain("test_index", 640_001, 64, True, "ivfflat") == True
            
            # n_lists = 256, trained
            # Threshold = 256 * 10000 = 2,560,000
            assert manager.should_retrain("test_index", 2_559_999, 256, True, "ivfflat") == False
            assert manager.should_retrain("test_index", 2_560_001, 256, True, "ivfflat") == True
    
    def test_is_training_tracking(self):
        """Test tracking of indexes being trained."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            
            # Initially no indexes are being trained
            assert manager.is_training("index1") == False
            assert manager.is_training("index2") == False
            
            # Add index to training set
            with manager._lock:
                manager._training_indexes.add("index1")
            
            assert manager.is_training("index1") == True
            assert manager.is_training("index2") == False
            
            # Remove from training set
            with manager._lock:
                manager._training_indexes.discard("index1")
            
            assert manager.is_training("index1") == False
    
    @pytest.mark.asyncio
    async def test_trigger_training_if_needed_below_threshold(self):
        """Test that training is not triggered when below threshold."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            manager._retrain_threshold = 10000
            manager._training_client = Mock()
            
            # Below threshold - should not trigger
            triggered = await manager.trigger_training_if_needed(
                index_name="test_index",
                index_key_hex="0" * 64,
                num_vectors=5000,
                n_lists=128,
                is_trained=False,
                index_type="ivfflat"
            )
            
            assert triggered == False
            assert manager.is_training("test_index") == False
            manager._training_client.load_index.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_trigger_training_already_training(self):
        """Test that training is not triggered if already in progress."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            manager._retrain_threshold = 10000
            
            # Mark index as already training
            with manager._lock:
                manager._training_indexes.add("test_index")
            
            # Should not trigger again
            triggered = await manager.trigger_training_if_needed(
                index_name="test_index",
                index_key_hex="0" * 64,
                num_vectors=15000,
                n_lists=128,
                is_trained=False,
                index_type="ivfflat"
            )
            
            assert triggered == False
            assert manager.is_training("test_index") == True
    
    def test_get_training_status(self):
        """Test getting the training status."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            manager._retrain_threshold = 10000
            
            # Add some indexes to training
            with manager._lock:
                manager._training_indexes.add("index1")
                manager._training_indexes.add("index2")
            
            status = manager.get_training_status()
            
            assert "training_indexes" in status
            assert "retrain_threshold" in status
            assert set(status["training_indexes"]) == {"index1", "index2"}
            assert status["retrain_threshold"] == 10000
    
    def test_custom_retrain_threshold(self):
        """Test custom retrain threshold from environment variable."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.dict('os.environ', {'RETRAIN_THRESHOLD': '5000'}):
            with patch.object(TrainingManager, '_initialize_training_client'):
                manager = TrainingManager()
                assert manager._retrain_threshold == 5000
                
                # Test with custom threshold
                # Threshold = 1 * 5000 = 5000 for untrained
                assert manager.should_retrain("test_index", 4999, 128, False, "ivfflat") == False
                assert manager.should_retrain("test_index", 5001, 128, False, "ivfflat") == True
    
    @pytest.mark.asyncio
    async def test_multiple_indexes_concurrent_training(self):
        """Test that different indexes can be tracked for training concurrently."""
        from cyborgdb_service.core.training_manager import TrainingManager
        
        with patch.object(TrainingManager, '_initialize_training_client'):
            manager = TrainingManager()
            manager._retrain_threshold = 10000
            
            # Mock the training client
            mock_index = Mock()
            mock_index.train = Mock()
            manager._training_client = Mock()
            manager._training_client.load_index.return_value = mock_index
            
            # Trigger training for first index
            triggered1 = await manager.trigger_training_if_needed(
                index_name="index1",
                index_key_hex="0" * 64,
                num_vectors=15000,
                n_lists=128,
                is_trained=False,
                index_type="ivfflat"
            )
            
            # Trigger training for second index
            triggered2 = await manager.trigger_training_if_needed(
                index_name="index2",
                index_key_hex="1" * 64,
                num_vectors=15000,
                n_lists=128,
                is_trained=False,
                index_type="ivfflat"
            )
            
            assert triggered1 == True
            assert triggered2 == True
            assert manager.is_training("index1") == True
            assert manager.is_training("index2") == True
            
            # Both should be in training status
            status = manager.get_training_status()
            assert set(status["training_indexes"]) == {"index1", "index2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
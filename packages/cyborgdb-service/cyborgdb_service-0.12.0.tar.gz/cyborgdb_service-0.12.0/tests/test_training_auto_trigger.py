"""
Tests for automatic training trigger functionality.

This module tests the automatic triggering of index training based on
vector count thresholds after upsert operations.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from cyborgdb_service.core.training_manager import TrainingManager, get_training_manager
from cyborgdb_service.api.routes.vectors import upsert_vectors
from cyborgdb_service.api.schemas.vectors import UpsertRequest


class TestTrainingManager:
    """Test the TrainingManager class functionality."""
    
    def test_should_retrain_untrained_index(self):
        """Test retraining logic for untrained indexes (n_lists=1)."""
        manager = TrainingManager()
        
        # For untrained index, effective n_lists = 1
        # Threshold = 1 * 10000 = 10000
        assert manager.should_retrain("test_index", 9999, 128, False, "ivfflat") == False
        assert manager.should_retrain("test_index", 10001, 128, False, "ivfflat") == True
        assert manager.should_retrain("test_index", 20000, 128, False, "ivfflat") == True
    
    def test_should_retrain_trained_index(self):
        """Test retraining logic for trained indexes."""
        manager = TrainingManager()
        
        # For trained ivfflat index with n_lists=128
        # Threshold = 128 * 10000 = 1,280,000
        assert manager.should_retrain("test_index", 1_000_000, 128, True, "ivfflat") == False
        assert manager.should_retrain("test_index", 1_280_001, 128, True, "ivfflat") == True
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "ivfflat") == True
    
    def test_should_retrain_various_n_lists(self):
        """Test retraining logic with various n_lists values."""
        manager = TrainingManager()
        
        # n_lists = 64, trained ivfflat
        # Threshold = 64 * 10000 = 640,000
        assert manager.should_retrain("test_index", 639_999, 64, True, "ivfflat") == False
        assert manager.should_retrain("test_index", 640_001, 64, True, "ivfflat") == True
        
        # n_lists = 256, trained ivfflat
        # Threshold = 256 * 10000 = 2,560,000
        assert manager.should_retrain("test_index", 2_559_999, 256, True, "ivfflat") == False
        assert manager.should_retrain("test_index", 2_560_001, 256, True, "ivfflat") == True
    
    def test_should_retrain_ivf_index_type_constraints(self):
        """Test index type constraints for IVF and IVFPQ indexes."""
        manager = TrainingManager()
        
        # IVF index - can train when untrained, cannot retrain when trained
        assert manager.should_retrain("ivf_index", 15000, 128, False, "ivf") == True  # Initial training allowed
        assert manager.should_retrain("ivf_index", 2_000_000, 128, True, "ivf") == False  # Retraining blocked
        
        # IVFPQ index - can train when untrained, cannot retrain when trained
        assert manager.should_retrain("ivfpq_index", 15000, 128, False, "ivfpq") == True  # Initial training allowed
        assert manager.should_retrain("ivfpq_index", 2_000_000, 128, True, "ivfpq") == False  # Retraining blocked
        
        # IVFFlat index - can train and retrain
        assert manager.should_retrain("ivfflat_index", 15000, 128, False, "ivfflat") == True  # Initial training allowed
        assert manager.should_retrain("ivfflat_index", 2_000_000, 128, True, "ivfflat") == True  # Retraining allowed
    
    def test_should_retrain_case_insensitive_index_types(self):
        """Test that index type checking is case insensitive."""
        manager = TrainingManager()
        
        # Test uppercase index types
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "IVF") == False
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "IVFPQ") == False
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "IVFFLAT") == True
        
        # Test mixed case index types
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "IvF") == False
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "IvfPq") == False
        assert manager.should_retrain("test_index", 2_000_000, 128, True, "IvfFlat") == True
    
    def test_is_training_tracking(self):
        """Test tracking of indexes being trained."""
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
        manager = TrainingManager()
        
        # Mock the training client
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
    async def test_trigger_training_if_needed_above_threshold(self):
        """Test that training is triggered when above threshold."""
        manager = TrainingManager()
        
        # Mock the training client and index
        mock_index = Mock()
        mock_index.train = Mock()
        manager._training_client = Mock()
        manager._training_client.load_index.return_value = mock_index
        
        # Above threshold - should trigger
        triggered = await manager.trigger_training_if_needed(
            index_name="test_index",
            index_key_hex="0" * 64,
            num_vectors=15000,
            n_lists=128,
            is_trained=False,
            index_type="ivfflat"
        )
        
        assert triggered == True
        assert manager.is_training("test_index") == True
        
        # Wait a bit for the training to start
        await asyncio.sleep(0.1)
        
        # Verify training was initiated
        manager._training_client.load_index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_training_already_training(self):
        """Test that training is not triggered if already in progress."""
        manager = TrainingManager()
        
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
        manager = TrainingManager()
        
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
        with patch.dict('os.environ', {'RETRAIN_THRESHOLD': '5000'}):
            manager = TrainingManager()
            assert manager._retrain_threshold == 5000
            
            # Test with custom threshold
            # Threshold = 1 * 5000 = 5000 for untrained
            assert manager.should_retrain("test_index", 4999, 128, False, "ivfflat") == False
            assert manager.should_retrain("test_index", 5001, 128, False, "ivfflat") == True
    
    @pytest.mark.asyncio
    async def test_trigger_training_blocked_for_trained_ivf_index(self):
        """Test that training is blocked for trained IVF/IVFPQ indexes."""
        manager = TrainingManager()
        
        # Mock the training client (shouldn't be called)
        manager._training_client = Mock()
        
        # Trained IVF index - should not trigger even if above threshold
        triggered = await manager.trigger_training_if_needed(
            index_name="test_index",
            index_key_hex="0" * 64,
            num_vectors=2_000_000,  # Well above threshold
            n_lists=128,
            is_trained=True,
            index_type="ivf"
        )
        
        assert triggered == False
        assert manager.is_training("test_index") == False
        manager._training_client.load_index.assert_not_called()
        
        # Trained IVFPQ index - should not trigger even if above threshold
        triggered = await manager.trigger_training_if_needed(
            index_name="test_index2",
            index_key_hex="0" * 64,
            num_vectors=2_000_000,  # Well above threshold
            n_lists=128,
            is_trained=True,
            index_type="ivfpq"
        )
        
        assert triggered == False
        assert manager.is_training("test_index2") == False


class TestUpsertWithAutoTrigger:
    """Test the upsert endpoint with auto-trigger functionality."""
    
    @pytest.mark.asyncio
    async def test_upsert_triggers_training(self):
        """Test that upsert triggers training when threshold is exceeded."""
        # Create request
        request = UpsertRequest(
            index_name="test_index",
            index_key="0" * 64,
            items=[
                {"id": f"item_{i}", "vector": [0.1] * 128}
                for i in range(100)
            ]
        )
        
        # Mock dependencies
        mock_client = Mock()
        mock_index = Mock()
        mock_index.upsert.return_value = None
        mock_index.get_num_vectors.return_value = 15000  # Above threshold
        mock_index.is_trained.return_value = False
        mock_index.index_config.return_value = {"n_lists": 128, "type": "ivfflat"}
        
        with patch('cyborgdb_service.api.routes.vectors.load_index', return_value=mock_index):
            with patch('cyborgdb_service.api.routes.vectors.get_training_manager') as mock_get_manager:
                mock_manager = Mock()
                mock_manager._retrain_threshold = 10000
                mock_manager.trigger_training_if_needed = AsyncMock(return_value=True)
                mock_get_manager.return_value = mock_manager
                
                # Call upsert
                response = await upsert_vectors(request, mock_client)
                
                # Verify upsert was called
                mock_index.upsert.assert_called_once()
                
                # Verify training was triggered
                mock_manager.trigger_training_if_needed.assert_called_once_with(
                    index_name="test_index",
                    index_key_hex="0" * 64,
                    num_vectors=15000,
                    n_lists=128,
                    is_trained=False,
                    index_type="ivfflat"
                )
                
                # Check response
                assert response["status"] == "success"
                assert "Upserted 100 vectors" in response["message"]
                assert response.get("training_triggered") == True
                assert "training_message" in response
    
    @pytest.mark.asyncio
    async def test_upsert_no_training_below_threshold(self):
        """Test that upsert doesn't trigger training when below threshold."""
        # Create request
        request = UpsertRequest(
            index_name="test_index",
            index_key="0" * 64,
            items=[
                {"id": f"item_{i}", "vector": [0.1] * 128}
                for i in range(10)
            ]
        )
        
        # Mock dependencies
        mock_client = Mock()
        mock_index = Mock()
        mock_index.upsert.return_value = None
        mock_index.get_num_vectors.return_value = 5000  # Below threshold
        mock_index.is_trained.return_value = False
        mock_index.index_config.return_value = {"n_lists": 128, "type": "ivfflat"}
        
        with patch('cyborgdb_service.api.routes.vectors.load_index', return_value=mock_index):
            with patch('cyborgdb_service.api.routes.vectors.get_training_manager') as mock_get_manager:
                mock_manager = Mock()
                mock_manager._retrain_threshold = 10000
                mock_manager.trigger_training_if_needed = AsyncMock(return_value=False)
                mock_get_manager.return_value = mock_manager
                
                # Call upsert
                response = await upsert_vectors(request, mock_client)
                
                # Verify upsert was called
                mock_index.upsert.assert_called_once()
                
                # Verify training check was called
                mock_manager.trigger_training_if_needed.assert_called_once()
                
                # Check response - no training triggered
                assert response["status"] == "success"
                assert "Upserted 10 vectors" in response["message"]
                assert "training_triggered" not in response
    
    @pytest.mark.asyncio
    async def test_upsert_training_check_failure(self):
        """Test that upsert succeeds even if training check fails."""
        # Create request
        request = UpsertRequest(
            index_name="test_index",
            index_key="0" * 64,
            items=[
                {"id": "item_1", "vector": [0.1] * 128}
            ]
        )
        
        # Mock dependencies
        mock_client = Mock()
        mock_index = Mock()
        mock_index.upsert.return_value = None
        mock_index.get_num_vectors.side_effect = Exception("Failed to get num vectors")
        
        with patch('cyborgdb_service.api.routes.vectors.load_index', return_value=mock_index):
            with patch('cyborgdb_service.api.routes.vectors.logger') as mock_logger:
                # Call upsert
                response = await upsert_vectors(request, mock_client)
                
                # Verify upsert was called
                mock_index.upsert.assert_called_once()
                
                # Check that warning was logged
                mock_logger.warning.assert_called_once()
                
                # Check response - upsert succeeded with warning
                assert response["status"] == "success"
                assert "Upserted 1 vectors" in response["message"]
                assert response.get("warning") == "Training check failed but upsert succeeded"


class TestTrainingStatusEndpoint:
    """Test the training status endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_training_status_endpoint(self):
        """Test the /indexes/training-status endpoint."""
        from cyborgdb_service.api.routes.indexes import get_training_status
        
        with patch('cyborgdb_service.api.routes.indexes.get_training_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_training_status.return_value = {
                "training_indexes": ["index1", "index2"],
                "retrain_threshold": 10000
            }
            mock_get_manager.return_value = mock_manager
            
            # Call endpoint
            response = await get_training_status()
            
            # Verify response
            assert response["training_indexes"] == ["index1", "index2"]
            assert response["retrain_threshold"] == 10000
            mock_manager.get_training_status.assert_called_once()


class TestIntegrationScenarios:
    """Integration test scenarios for auto-trigger functionality."""
    
    @pytest.mark.asyncio
    async def test_auto_training_trigger_for_untrained_index(self):
        """Test that auto training is triggered when threshold is exceeded for untrained index."""
        manager = TrainingManager()
        
        # Mock the training client and index
        mock_index = Mock()
        mock_index.train = Mock()
        manager._training_client = Mock()
        manager._training_client.load_index.return_value = mock_index
        
        # Simulate an untrained index reaching the threshold
        # For untrained index, threshold = 1 * 10000 = 10000
        triggered = await manager.trigger_training_if_needed(
            index_name="new_index",
            index_key_hex="a" * 64,
            num_vectors=10001,  # Just above threshold
            n_lists=128,
            is_trained=False,
            index_type="ivfflat"
        )
        
        assert triggered == True
        assert manager.is_training("new_index") == True
        
        # Wait for training to start
        await asyncio.sleep(0.1)
        
        # Verify training was initiated
        manager._training_client.load_index.assert_called_once_with(
            index_name="new_index",
            index_key=b'\xaa' * 32  # hex_to_bytes("a" * 64)
        )
    
    @pytest.mark.asyncio
    async def test_auto_retraining_only_for_ivfflat(self):
        """Test that auto retraining is triggered only for ivfflat indexes when already trained."""
        manager = TrainingManager()
        
        # Mock the training client and index
        mock_index = Mock()
        mock_index.train = Mock()
        manager._training_client = Mock()
        manager._training_client.load_index.return_value = mock_index
        
        # Test 1: IVFFlat - should allow retraining when trained
        triggered_ivfflat = await manager.trigger_training_if_needed(
            index_name="ivfflat_trained",
            index_key_hex="b" * 64,
            num_vectors=1_280_001,  # Above threshold for n_lists=128
            n_lists=128,
            is_trained=True,  # Already trained
            index_type="ivfflat"
        )
        
        assert triggered_ivfflat == True
        assert manager.is_training("ivfflat_trained") == True
        
        # Test 2: IVF - should NOT allow retraining when trained
        triggered_ivf = await manager.trigger_training_if_needed(
            index_name="ivf_trained",
            index_key_hex="c" * 64,
            num_vectors=2_000_000,  # Well above threshold
            n_lists=128,
            is_trained=True,  # Already trained
            index_type="ivf"
        )
        
        assert triggered_ivf == False
        assert manager.is_training("ivf_trained") == False
        
        # Test 3: IVFPQ - should NOT allow retraining when trained
        triggered_ivfpq = await manager.trigger_training_if_needed(
            index_name="ivfpq_trained",
            index_key_hex="d" * 64,
            num_vectors=2_000_000,  # Well above threshold
            n_lists=128,
            is_trained=True,  # Already trained
            index_type="ivfpq"
        )
        
        assert triggered_ivfpq == False
        assert manager.is_training("ivfpq_trained") == False
        
        # Wait for any async operations
        await asyncio.sleep(0.1)
        
        # Verify that only ivfflat triggered training
        assert manager._training_client.load_index.call_count == 1
        manager._training_client.load_index.assert_called_once_with(
            index_name="ivfflat_trained",
            index_key=b'\xbb' * 32  # hex_to_bytes("b" * 64)
        )
    
    @pytest.mark.asyncio
    async def test_multiple_upserts_trigger_once(self):
        """Test that multiple rapid upserts only trigger training once."""
        manager = TrainingManager()
        
        # Mock the training client
        mock_index = Mock()
        mock_index.train = Mock()
        manager._training_client = Mock()
        manager._training_client.load_index.return_value = mock_index
        
        # First upsert triggers training
        triggered1 = await manager.trigger_training_if_needed(
            index_name="test_index",
            index_key_hex="0" * 64,
            num_vectors=15000,
            n_lists=128,
            is_trained=False,
            index_type="ivfflat"
        )
        
        # Second upsert should not trigger (already training)
        triggered2 = await manager.trigger_training_if_needed(
            index_name="test_index",
            index_key_hex="0" * 64,
            num_vectors=16000,
            n_lists=128,
            is_trained=False,
            index_type="ivfflat"
        )
        
        assert triggered1 == True
        assert triggered2 == False
        assert manager.is_training("test_index") == True
    
    @pytest.mark.asyncio
    async def test_concurrent_indexes_training(self):
        """Test that different indexes can be trained concurrently."""
        manager = TrainingManager()
        
        # Mock the training client
        mock_index = Mock()
        mock_index.train = Mock()
        manager._training_client = Mock()
        manager._training_client.load_index.return_value = mock_index
        
        # Trigger training for multiple indexes
        triggered1 = await manager.trigger_training_if_needed(
            index_name="index1",
            index_key_hex="0" * 64,
            num_vectors=15000,
            n_lists=128,
            is_trained=False,
            index_type="ivfflat"
        )
        
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
"""
Tests for the list_ids endpoint functionality.
"""
import pytest
from unittest.mock import Mock, patch

from cyborgdb_service.api.routes.vectors import list_ids
from cyborgdb_service.api.schemas.vectors import ListIDsRequest, ListIDsResponse


class TestListIDsEndpoint:
    """Test the list_ids endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_list_ids_endpoint(self):
        """Test that list_ids endpoint correctly calls the core function and returns response."""
        # Create request
        request = ListIDsRequest(
            index_name="test_index",
            index_key="0" * 64
        )
        
        # Mock dependencies
        mock_client = Mock()
        mock_index = Mock()
        mock_index.list_ids.return_value = ["id1", "id2", "id3", "id4", "id5"]
        
        with patch('cyborgdb_service.api.routes.vectors.load_index', return_value=mock_index):
            # Call list_ids endpoint
            response = await list_ids(request, mock_client)
            
            # Verify the index method was called
            mock_index.list_ids.assert_called_once()
            
            # Check response format
            assert isinstance(response, ListIDsResponse)
            assert response.ids == ["id1", "id2", "id3", "id4", "id5"]
            assert response.count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
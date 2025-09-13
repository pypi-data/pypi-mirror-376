from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
import logging

from cyborgdb_service.api.deps import get_current_client, get_index
from cyborgdb_service.core.security import hex_to_bytes
from cyborgdb_service.db.client import create_index_config, load_index
from cyborgdb_service.core.training_manager import get_training_manager
from cyborgdb_service.api.schemas.index import (
    CreateIndexRequest, 
    TrainRequest,
    IndexOperationRequest,
    IndexInfoResponse,
    IndexListResponse,
    IndexTrainingStatusResponse,
    CreateResponses,
    TrainResponses,
    DeleteIndexResponses
)
from cyborgdb_service.utils.error_handler import handle_exception

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/indexes")

@router.get("/list", summary="List Encrypted Indexes",
responses = IndexListResponse)
async def list_indexes(client = Depends(get_current_client)):
    """
    List all available indexes.
    """
    try:
        indexes = client.list_indexes()
        return {"indexes": indexes}
    except Exception as e:
        handle_exception(e,"Failed to list indexes")

@router.post("/create",  summary="Create Encrypted Index",responses = CreateResponses)
async def create_index(
 
    request: CreateIndexRequest, 
    client = Depends(get_current_client)
):
    """
    Create a new encrypted index with the provided configuration.
    """
    # Convert hex key to bytes
    index_key = hex_to_bytes(request.index_key)
    
    # Create the appropriate index config
    index_config = create_index_config(request.index_config)
    
    try:
        # Create the index
        client.create_index(
            index_name=request.index_name,
            index_key=index_key,
            index_config=index_config,
            embedding_model=request.embedding_model,
            metric=request.metric
        )
        
        return {
            "status": "success",
            "message": f"Index '{request.index_name}' created successfully"
        }
    except Exception as e:
        handle_exception(e,"Failed to create index")

@router.post("/describe", summary="Describe Encrypted Index",responses = IndexInfoResponse)
async def get_index_info(
    request: IndexOperationRequest = Body(...),
    client = Depends(get_current_client)
):
    """
    Get information about a specific index.
    """
    index = load_index(request.index_name, request.index_key)
    
    return {
        "index_name": index.index_name(),
        "index_type": index.index_type(),
        "is_trained": index.is_trained(),
        "index_config": index.index_config()
    }

@router.post("/delete", summary="Delete Encrypted Index",responses = DeleteIndexResponses)
async def delete_index(
    request: IndexOperationRequest = Body(...),
    client = Depends(get_current_client)
):
    """
    Delete a specific index.
    """
    index = load_index(request.index_name, request.index_key)
    
    try:
        index.delete_index()
        
        return {
            "status": "success",
            "message": f"Index '{request.index_name}' deleted successfully"
        }
    except Exception as e:
        handle_exception(e,"Failed to delete index")

# NOTE decide to either pick backgroundtask (fastapi) or adding a threads for the train index fuction since it takes a long time to run
# TODO
@router.post("/train", summary="Train Encrypted index",responses = TrainResponses)
async def train_index(
    request: TrainRequest,
    client = Depends(get_current_client)
):
    """
    Train the index for efficient querying.
    
    Note: This endpoint triggers manual training. Automatic training is also
    triggered based on vector count thresholds after upserts.
    """
    index = load_index(request.index_name, request.index_key)
    
    # Check if already being trained by auto-trigger
    training_manager = get_training_manager()
    if training_manager.is_training(request.index_name):
        return {
            "status": "in_progress",
            "message": f"Index '{request.index_name}' is already being trained"
        }
    
    try:
        index.train(
            n_lists=request.n_lists,
            batch_size=request.batch_size,
            max_iters=request.max_iters,
            tolerance=request.tolerance,
            max_memory=request.max_memory
        )
        return {
            "status": "success",
            "message": f"Index '{request.index_name}' trained successfully"
        }
    except Exception as e:
        handle_exception(e,"Failed to train index")

@router.get("/training-status", summary="Get Training Status", responses=IndexTrainingStatusResponse)
async def get_training_status():
    """
    Get the current training status including indexes being trained
    and the retrain threshold configuration.
    
    Returns:
        dict: Training status information including:
            - training_indexes: List of index names currently being trained
            - retrain_threshold: The multiplier used for the retraining threshold
    """
    try:
        training_manager = get_training_manager()
        return training_manager.get_training_status()
    except Exception as e:
        handle_exception(e, "Failed to get training status")

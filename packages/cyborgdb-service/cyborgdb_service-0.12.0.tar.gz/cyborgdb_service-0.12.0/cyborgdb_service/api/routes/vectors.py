from typing import Dict, List, Union, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from fastapi.encoders import jsonable_encoder
import asyncio
import logging

from cyborgdb_service.api.deps import get_current_client
from cyborgdb_service.db.client import load_index
from cyborgdb_service.api.schemas.vectors import (
    UpsertRequest,
    QueryRequest,
    BatchQueryRequest,
    IndexOperationRequest,
    GetRequest,
    DeleteRequest,
    ListIDsRequest,
    ListIDsResponse,
    QueryResponses,
    UpsertResponses,
    DeleteResponses,
    NumVectorsResponses,
    GetResponses
)
from cyborgdb_service.utils.error_handler import handle_exception
from cyborgdb_service.core.training_manager import get_training_manager
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vectors")

@router.post("/upsert", summary="Add Items to Encrypted Index",responses = UpsertResponses)
async def upsert_vectors(
    request: UpsertRequest,
    client = Depends(get_current_client)
):
    """
    Add or update vectors in the index.
    
    After upserting, checks if the index needs training/retraining based on the
    number of vectors and triggers automatic training if needed.
    """
    index = load_index(request.index_name, request.index_key)
    items = jsonable_encoder(request.items,exclude_none=True)
    try:
        # Perform the upsert
        index.upsert(items)
        
        # Check if training is needed after upsert
        try:
            # Get current index state
            num_vectors = index.get_num_vectors()
            is_trained = index.is_trained()
            index_config = index.index_config()
            n_lists = index_config.get('n_lists', 0)
            index_type = index_config.get('type', 'unknown')
            
            # Trigger training check asynchronously
            training_manager = get_training_manager()
            training_triggered = await training_manager.trigger_training_if_needed(
                index_name=request.index_name,
                index_key_hex=request.index_key,
                num_vectors=num_vectors,
                n_lists=n_lists,
                is_trained=is_trained,
                index_type=index_type
            )
            
            response = {
                "status": "success",
                "message": f"Upserted {len(items)} vectors"
            }
            
            if training_triggered:
                response["training_triggered"] = True
                response["training_message"] = f"Index training has been triggered (vectors: {num_vectors}, threshold: {n_lists * training_manager._retrain_threshold})"
            
            return response
            
        except Exception as training_error:
            # Log training check error but don't fail the upsert
            logger.warning(f"Failed to check training requirements after upsert: {str(training_error)}")
            return {
                "status": "success",
                "message": f"Upserted {len(items)} vectors",
                "warning": "Training check failed but upsert succeeded"
            }
            
    except Exception as e:
        handle_exception(e,"Failed to upsert vectors")

@router.post("/query", summary="Query Encrypted Index", responses=QueryResponses)
async def query_vectors(
    request: Union[QueryRequest, BatchQueryRequest],
    client = Depends(get_current_client)
):
    """
    Search for nearest neighbors in the index.
    """
    index = load_index(request.index_name, request.index_key)
    
    try:
        # Check if this is a batch query by examining the structure of query_vectors
        if request.query_vectors and isinstance(request.query_vectors[0], list):
            # Batch query - 2D array (List[List[float]])
            query_vectors = np.array(request.query_vectors, dtype=np.float32)
            results = index.query(
                query_vectors=query_vectors,
                top_k=request.top_k,
                n_probes=request.n_probes,
                greedy=request.greedy,
                filters=request.filters,
                include=request.include
            )
        else:
            # Single query - either 1D vector or text content
            query_vectors = np.array(request.query_vectors, dtype=np.float32) if request.query_vectors else None
            results = index.query(
                query_vectors=query_vectors,
                query_contents=request.query_contents,
                top_k=request.top_k,
                n_probes=request.n_probes,
                greedy=request.greedy,
                filters=request.filters,
                include=request.include
            )
        
        return {"results": results}
    except Exception as e:
        handle_exception(e, "Failed to query")
        
@router.post("/get", summary="Get Items from Encrypted Index",responses = GetResponses)
async def get_vectors(
    request: GetRequest,
    client = Depends(get_current_client)
):
    """
    Retrieve vectors by their IDs.
    """
    index = load_index(request.index_name, request.index_key)
    
    try:
        items = index.get(ids=request.ids, include=request.include)
        return {"results": items}
    except Exception as e:
        handle_exception(e,"Failed to retrieve items")

@router.post("/delete", summary="Delete Items from Encrypted Index",responses= DeleteResponses)
async def delete_vectors(
    request: DeleteRequest,
    client = Depends(get_current_client)
):
    """
    Delete vectors by their IDs.
    """
    index = load_index(request.index_name, request.index_key)
    
    try:
        index.delete(request.ids)
        return {
            "status": "success",
            "message": f"Deleted {len(request.ids)} vectors"
        }
    except Exception as e:
        handle_exception(e,"Failed to delete items")


@router.post("/list_ids", summary="List all IDs in an index")
async def list_ids(
    request: ListIDsRequest = Body(...),
    client = Depends(get_current_client)
) -> ListIDsResponse:
    """
    List all item IDs currently stored in the index.
    
    Returns a list of all IDs and the total count.
    """
    index = load_index(request.index_name, request.index_key)
    
    try:
        ids = index.list_ids()
        return ListIDsResponse(ids=ids, count=len(ids))
    except Exception as e:
        handle_exception(e, "Failed to list IDs from index")

@router.post("/num_vectors", summary="Get the number of vectors in an index", responses = NumVectorsResponses)
async def get_index_size(
    request: IndexOperationRequest = Body(...),
    client = Depends(get_current_client)
):
    """
    Get the number of vectors stored in an index
    """
    index = load_index(request.index_name, request.index_key)

    try:
        result = index.get_num_vectors()
        return {"result": result}
    except Exception as e:
        handle_exception(e,"Failed to get size of index")

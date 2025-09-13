from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field

# ============================
# Base Index Configuration Models
# ============================

class IndexConfigBase(BaseModel):
    """
    Base model for index configuration.
    
    Attributes:
        dimension (Optional[int]): The dimensionality of the vectors.
    """
    dimension: Optional[int] = None


class IndexIVFModel(IndexConfigBase):
    """
    Model for configuring an IVF (Inverted File) index.
    
    Attributes:
        type (str): Index type identifier. Defaults to "ivf".
    """
    type: str = "ivf"


class IndexIVFPQModel(IndexConfigBase):
    """
    Model for configuring an IVFPQ (Inverted File with Product Quantization) index.
    
    Attributes:
        type (str): Index type identifier. Defaults to "ivfpq".
        pq_dim (int): Dimensionality of PQ codes.
        pq_bits (int): Number of bits per quantizer.
    """
    type: str = "ivfpq"
    pq_dim: int
    pq_bits: int


class IndexIVFFlatModel(IndexConfigBase):
    """
    Model for configuring an IVFFlat (Inverted File with Flat quantization) index.
    
    Attributes:
        type (str): Index type identifier. Defaults to "ivfflat".
    """
    type: str = "ivfflat"


# ============================
# API Request Models
# ============================

class CreateIndexRequest(BaseModel):
    """
    Request model for creating a new encrypted index.
    
    Attributes:
        index_config (Optional[Union[IndexIVFModel, IndexIVFPQModel, IndexIVFFlatModel]]): 
            Optional configuration model for the index.
        index_key (str): A 32-byte encryption key as a hex string.
        index_name (str): The name/identifier of the index.
        embedding_model (Optional[str]): Optional embedding model name.
        metric (Optional[str]): Optional distance metric.
    """
    index_config: Optional[Union[IndexIVFModel, IndexIVFPQModel, IndexIVFFlatModel]] = None
    index_key: str = Field(..., description="32-byte encryption key as hex string")
    index_name: str = Field(..., description="ID name")
    embedding_model: Optional[str] = None
    metric: Optional[str] = None


class IndexOperationRequest(BaseModel):
    """
    Request model for performing operations on an existing index (e.g., delete, describe).
    
    Attributes:
        index_key (str): A 32-byte encryption key as a hex string.
        index_name (str): The name/identifier of the index.
    """
    index_key: str = Field(..., description="32-byte encryption key as hex string")
    index_name: str = Field(..., description="ID name")


class TrainRequest(IndexOperationRequest):
    """
    Request model for training an index.
    
    Attributes:
        n_lists (Optional[int]): Number of lists/clusters for the index. Default is auto.
        batch_size (Optional[int]): Size of each batch for training. Default is 2048.
        max_iters (Optional[int]): Maximum iterations for training. Default is 100.
        tolerance (Optional[float]): Convergence tolerance for training. Default is 1e-6.
        max_memory (Optional[int]): Maximum memory (MB) usage during training. Default is 0 (no limit).
    """
    n_lists: Optional[int] = None
    batch_size: Optional[int] = None
    max_iters: Optional[int] = None
    tolerance: Optional[float] = None
    max_memory: Optional[int] = None


# ============================
# API Response Models
# ============================

class IndexListResponseModel(BaseModel):
    """
    Response model for listing all indexes.
    
    Attributes:
        indexes (List[str]): List of available index names.
    """
    indexes: List[str]


class IndexInfoResponseModel(BaseModel):
    """
    Response model for retrieving information about an index.
    
    Attributes:
        index_name (str): The name of the index.
        index_type (str): The type of index (e.g., IVF, IVFFlat, IVFPQ).
        is_trained (bool): Indicates whether the index has been trained.
        index_config (Dict[str, Any]): The full configuration details of the index.
    """
    index_name: str
    index_type: str
    is_trained: bool
    index_config: Dict[str, Any]

class IndexTrainingStatusResponseModel(BaseModel):
    """
    Response model for retrieving the training status of indexes.
    
    Attributes:
        training_indexes (List[str]): List of index names currently being trained.
        retrain_threshold (int): The multiplier used for the retraining threshold.
    """
    training_indexes: List[str]
    retrain_threshold: int
    worker_pid: int
    global_training: Dict[str, Any]

# ============================
# Standard Response Models
# ============================

class SuccessResponseModel(BaseModel):
    """
    Standard success response model.
    
    Attributes:
        status (str): The status of the response. Defaults to "success".
        message (str): A success message.
    """
    status: str = "success"
    message: str

class ErrorResponseModel(BaseModel):
    """
    Standard error response model.

    Attributes:
        status_code (int): HTTP status code of the error.
        detail (str): A detailed message describing the error.
    """
    status_code: int
    detail: str



# ============================
# API Response Dictionary
# ============================
ErrorResponses: Dict[int, Dict] = {
    401: {"description": "Permission denied from license issue", "model": ErrorResponseModel},
    500: {"description": "Unexpected server error", "model": ErrorResponseModel},
}

CreateResponses: Dict[int, Dict] = {
    **ErrorResponses,  # Inherit standard responses
    200: {"description": "Successful response", "model": SuccessResponseModel},
    409: {"description": "Conflict for index name", "model": ErrorResponseModel},

}

TrainResponses: Dict[int, Dict] = {
    **ErrorResponses,
    200: {"description": "Successful response", "model": SuccessResponseModel},
}

DeleteIndexResponses: Dict[int, Dict] = {
    **ErrorResponses,
    200: {"description": "Successful response", "model": SuccessResponseModel},
    404: {"description": "Not able to find index", "model": ErrorResponseModel},
}

IndexInfoResponse: Dict[int, Dict] = {
    **ErrorResponses,
    200: {"description": "Successful response", "model": IndexInfoResponseModel},
    404: {"description": "Not able to find index", "model": ErrorResponseModel},
}

IndexListResponse: Dict[int, Dict] = {
    **ErrorResponses,
    200: {"description": "Successful response", "model": IndexListResponseModel},
}

IndexTrainingStatusResponse: Dict[int, Dict] = {
    **ErrorResponses,
    200: {"description": "Successful response", "model": IndexTrainingStatusResponseModel},
}
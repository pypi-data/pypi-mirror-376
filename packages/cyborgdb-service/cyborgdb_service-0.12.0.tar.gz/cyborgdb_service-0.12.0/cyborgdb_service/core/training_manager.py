"""
Training Manager for CyborgDB Service

This module manages automatic index training/retraining based on vector count thresholds.
It maintains a dedicated training client and tracks indexes currently being trained.
"""
import threading
import logging
from typing import Set, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio
from fastapi import HTTPException
import os
from cyborgdb_service.core.training_lock import TrainingLock

try:
    import cyborgdb_core as cyborgdb
    from cyborgdb_core import Client, DBConfig
except ImportError:
    import cyborgdb_lite as cyborgdb
    from cyborgdb_lite import Client, DBConfig

from cyborgdb_service.core.config import settings
from cyborgdb_service.core.security import hex_to_bytes

logger = logging.getLogger(__name__)


class TrainingManager:
    """Manages index training operations with a dedicated client and thread pool."""
    
    # Default retraining threshold - trigger when num_vectors > n_lists * threshold
    DEFAULT_RETRAIN_THRESHOLD = 10000
    
    def __init__(self):
        """Initialize the training manager."""
        self._lock = threading.Lock()
        self._training_indexes: Set[str] = set()
        self._training_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="training")
        self._training_client: Optional[Client] = None
        self._retrain_threshold = int(os.getenv("RETRAIN_THRESHOLD", self.DEFAULT_RETRAIN_THRESHOLD))
        
        # Initialize the cross-process training lock
        self._training_lock = TrainingLock()
        
        # Initialize the dedicated training client
        self._initialize_training_client()
        
        # Clean up any stale locks on startup
        self._training_lock.cleanup_stale_locks()
        
        logger.info(f"TrainingManager initialized with retrain threshold: {self._retrain_threshold} (PID: {os.getpid()})")
    
    def _initialize_training_client(self):
        """Initialize a dedicated client for training operations with resource limits."""
        try:
            # Calculate resource limits for training client
            # Use a small portion of available resources to not degrade server performance
            training_cpu_threads = max(1, settings.CPU_THREADS // 4) if settings.CPU_THREADS > 0 else 2
            
            index_location = DBConfig(
                location=settings.INDEX_LOCATION,
                table_name=settings.INDEX_TABLE_NAME,
                connection_string=settings.INDEX_CONNECTION_STRING,
            )
            config_location = DBConfig(
                location=settings.CONFIG_LOCATION,
                table_name=settings.CONFIG_TABLE_NAME,
                connection_string=settings.CONFIG_CONNECTION_STRING,
            )
            items_location = DBConfig(
                location=settings.ITEMS_LOCATION,
                table_name=settings.ITEMS_TABLE_NAME,
                connection_string=settings.ITEMS_CONNECTION_STRING,
            )
            
            self._training_client = Client(
                api_key=settings.CYBORGDB_API_KEY,
                index_location=index_location,
                config_location=config_location,
                items_location=items_location,
                cpu_threads=training_cpu_threads,
                gpu_accelerate=False  # Disable GPU for training client to conserve resources
            )
            
            logger.info(f"Training client initialized with {training_cpu_threads} CPU threads")
            
        except Exception as e:
            logger.error(f"Failed to initialize training client: {str(e)}")
            raise
    
    def should_retrain(self, index_name: str, num_vectors: int, n_lists: int, is_trained: bool, index_type: str) -> bool:
        """
        Check if an index should be retrained based on the heuristic and index type.
        
        Args:
            index_name: Name of the index
            num_vectors: Current number of vectors in the index
            n_lists: Number of lists in the index configuration
            is_trained: Whether the index is currently trained
            index_type: Type of the index (ivf, ivfpq, ivfflat)
            
        Returns:
            True if the index should be (re)trained, False otherwise
        """
        # Check index type constraints
        if index_type.lower() in ["ivf", "ivfpq"] and is_trained:
            logger.info(
                f"Index '{index_name}' type '{index_type}' cannot be retrained (already trained)"
            )
            return False
        
        # For ivfflat, allow retraining even if already trained
        # Use n_lists = 1 for untrained indexes as per requirement
        effective_n_lists = n_lists if is_trained else 1
        
        threshold = effective_n_lists * self._retrain_threshold
        should_train = num_vectors > threshold
        
        if should_train:
            action = "retraining" if is_trained else "training"
            logger.info(
                f"Index '{index_name}' (type: {index_type}) meets {action} criteria: "
                f"{num_vectors} vectors > {threshold} threshold "
                f"(n_lists={effective_n_lists}, trained={is_trained})"
            )
        
        return should_train
    
    def is_training(self, index_name: str) -> bool:
        """Check if an index is currently being trained."""
        with self._lock:
            return index_name in self._training_indexes
    
    async def trigger_training_if_needed(
        self, 
        index_name: str, 
        index_key_hex: str,
        num_vectors: int,
        n_lists: int,
        is_trained: bool,
        index_type: str
    ) -> bool:
        """
        Check if training is needed and trigger it asynchronously if so.
        
        Args:
            index_name: Name of the index
            index_key_hex: Hex-encoded encryption key for the index
            num_vectors: Current number of vectors
            n_lists: Number of lists in index config
            is_trained: Whether index is currently trained
            index_type: Type of the index (ivf, ivfpq, ivfflat)
            
        Returns:
            True if training was triggered, False otherwise
        """
        # Check if training is needed
        if not self.should_retrain(index_name, num_vectors, n_lists, is_trained, index_type):
            return False
        
        # Check if already training (local check first for performance)
        if self.is_training(index_name):
            logger.info(f"Index '{index_name}' is already being trained by this worker, skipping")
            return False
        
        # Check if any training is happening across all processes
        if self._training_lock.is_training_locked():
            training_info = self._training_lock.get_training_info()
            if training_info:
                logger.info(
                    f"Training already in progress for index '{training_info.get('index_name')}' "
                    f"by PID {training_info.get('pid')}, skipping training for '{index_name}'"
                )
            else:
                logger.info(f"Global training lock is held, skipping training for '{index_name}'")
            return False
        
        # Mark as training locally
        with self._lock:
            self._training_indexes.add(index_name)
        
        # Submit training job to executor
        future = self._training_executor.submit(
            self._train_index,
            index_name,
            index_key_hex
        )
        
        # Handle completion asynchronously
        asyncio.create_task(self._handle_training_completion(index_name, future))
        
        return True
    
    def _train_index(self, index_name: str, index_key_hex: str):
        """
        Perform the actual training operation (runs in executor thread).
        
        Args:
            index_name: Name of the index to train
            index_key_hex: Hex-encoded encryption key
        """
        try:
            # Acquire cross-process lock before training
            with self._training_lock.acquire_training_lock(index_name, timeout=10.0):
                logger.info(f"Starting training for index '{index_name}' (PID: {os.getpid()})")
                
                # Load the index with the training client
                index_key = hex_to_bytes(index_key_hex)
                index = self._training_client.load_index(
                    index_name=index_name,
                    index_key=index_key
                )
                
                # Perform training with reasonable defaults
                # These can be made configurable later if needed
                index.train(
                    batch_size=2048,
                    max_iters=100,
                    tolerance=1e-6,
                    max_memory=1024  # Limit memory usage to 1GB
                )
                
            
        except TimeoutError as e:
            logger.warning(f"Could not acquire training lock for index '{index_name}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Training failed for index '{index_name}': {str(e)}")
            raise
    
    async def _handle_training_completion(self, index_name: str, future):
        """
        Handle the completion of a training job.
        
        Args:
            index_name: Name of the index being trained
            future: Future object for the training task
        """
        try:
            # Wait for training to complete
            await asyncio.get_event_loop().run_in_executor(None, future.result)
            logger.info(f"Training completed successfully for index '{index_name}'")
        except Exception as e:
            logger.error(f"Training failed for index '{index_name}': {str(e)}")
        finally:
            # Remove from training set
            with self._lock:
                self._training_indexes.discard(index_name)
    
    def get_training_status(self) -> dict:
        """Get the current training status including cross-process information."""
        with self._lock:
            status = {
                "training_indexes": list(self._training_indexes),
                "retrain_threshold": self._retrain_threshold,
                "worker_pid": os.getpid()
            }
        
        # Add cross-process training info
        if self._training_lock.is_training_locked():
            training_info = self._training_lock.get_training_info()
            if training_info:
                status["global_training"] = {
                    "index_name": training_info.get("index_name"),
                    "pid": training_info.get("pid"),
                    "timestamp": training_info.get("timestamp"),
                    "worker_id": training_info.get("worker_id")
                }
        else:
            status["global_training"] = {}

        return status
    
    def shutdown(self):
        """Shutdown the training manager and cleanup resources."""
        logger.info(f"Shutting down TrainingManager (PID: {os.getpid()})")
        
        # Shutdown the executor
        self._training_executor.shutdown(wait=True)
        
        # Clean up any stale locks
        self._training_lock.cleanup_stale_locks(max_age_seconds=0)  # Clean all locks on shutdown


# Global training manager instance
_training_manager: Optional[TrainingManager] = None


def get_training_manager() -> TrainingManager:
    """Get or create the global training manager instance."""
    global _training_manager
    if _training_manager is None:
        _training_manager = TrainingManager()
    return _training_manager


def shutdown_training_manager():
    """Shutdown the global training manager."""
    global _training_manager
    if _training_manager is not None:
        _training_manager.shutdown()
        _training_manager = None
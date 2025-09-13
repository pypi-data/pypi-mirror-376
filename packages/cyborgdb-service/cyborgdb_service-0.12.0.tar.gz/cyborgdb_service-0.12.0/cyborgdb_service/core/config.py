# cyborgdb_service/core/config.py
import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

class Settings(BaseSettings):
    # API configuration
    APP_NAME: str = "CyborgDB Service"
    APP_DESCRIPTION: str = "REST API for CyborgDB: The Confidential Vector Database"
    APP_VERSION: str = "0.12.0"
    API_VERSION: str = "v1"

    @property
    def API_PREFIX(self) -> str:
        """Construct the API prefix dynamically based on the API version."""
        return f"/{self.API_VERSION}"
    
    # Server configuration
    PORT: int = 8000
    
    # SSL/HTTPS Configuration - simple path-based approach
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None

    @property
    def is_https_enabled(self) -> bool:
        """Check if HTTPS is enabled via certificate path"""
        return (self.SSL_CERT_PATH is not None and 
                self.SSL_KEY_PATH is not None and
                os.path.exists(self.SSL_CERT_PATH) and 
                os.path.exists(self.SSL_KEY_PATH))
    
    # Security
    REQUIRE_API_KEY: bool = True
    CYBORGDB_API_KEY: Optional[str] = None
    
    # Logging
    CYBORGDB_SERVICE_LOG_LEVEL: str = "INFO"

    # Make sure these are settable via .env file
    CYBORGDB_DB_TYPE: Optional[str] = None
    CYBORGDB_CONNECTION_STRING: Optional[str] = None
    
    # CyborgDB configuration
    INDEX_LOCATION: Optional[str] = None
    CONFIG_LOCATION: Optional[str] = None
    ITEMS_LOCATION: Optional[str] = None
    INDEX_TABLE_NAME: str = "index"
    CONFIG_TABLE_NAME: str = "config"
    ITEMS_TABLE_NAME: str = "items"
    INDEX_CONNECTION_STRING: Optional[str] = None
    CONFIG_CONNECTION_STRING: Optional[str] = None
    ITEMS_CONNECTION_STRING: Optional[str] = None
    CPU_THREADS: int = 0
    GPU_ACCELERATE: bool = False

    # Concurrency settings
    WORKERS: int = 0  # 0 means auto-calculate based on CPU count

    # Replace the Config class with model_config
    model_config = SettingsConfigDict(env_file=".env")

    # Set fallbacks for locations and connection strings
    @model_validator(mode='after')
    def set_fallbacks(self):
        self.INDEX_LOCATION = self.INDEX_LOCATION or self.CYBORGDB_DB_TYPE
        self.CONFIG_LOCATION = self.CONFIG_LOCATION or self.CYBORGDB_DB_TYPE
        self.ITEMS_LOCATION = self.ITEMS_LOCATION or self.CYBORGDB_DB_TYPE
        self.INDEX_CONNECTION_STRING = self.INDEX_CONNECTION_STRING or self.CYBORGDB_CONNECTION_STRING
        self.CONFIG_CONNECTION_STRING = self.CONFIG_CONNECTION_STRING or self.CYBORGDB_CONNECTION_STRING
        self.ITEMS_CONNECTION_STRING = self.ITEMS_CONNECTION_STRING or self.CYBORGDB_CONNECTION_STRING
        return self

def ensure_api_key():
    """Ensure we have an API key, generating one if necessary."""
    # Check environment variable
    if key := os.getenv("SERVICE_API_KEY"):
        return key
    
    # Check anything else

    # Generate a new API key
    key = secrets.token_urlsafe(32)
    os.environ["SERVICE_API_KEY"] = key

    print("\n   API Key Generated")
    print(f"   Key: {key}")
    print(f"   Saved to environment variable: SERVICE_API_KEY")
    print("   To disable auth: REQUIRE_API_KEY=false\n")
        
settings = Settings()
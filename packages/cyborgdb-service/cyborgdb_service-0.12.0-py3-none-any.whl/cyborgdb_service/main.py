# cyborgdb_service/main.py
import os
import sys
import logging
import uvicorn
from .package_installer import install_cyborgdb_core, verify_installation
from .utils.environment_check import print_usage_and_exit, ensure_environment_variables
from cyborgdb_service.core.config import settings

# Set environment variable first
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Setup logging
log_level = settings.CYBORGDB_SERVICE_LOG_LEVEL.upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("Logging level set to: %s", log_level)

def install_packages():
    """Install required packages with cloud version checking"""
    try:
        logger.info("Checking CyborgDB package versions...")
        successful = install_cyborgdb_core()
        
        # Verify installation
        verify_installation()
        
        if successful:
            logger.info("CyborgDB Core package ready")
        else:
            logger.info("CyborgDB Lite package ready")
            
    except Exception as e:
        logger.error(f"Package installation failed: {e}")
        sys.exit(1)

def main():
    """Main application entry point"""
    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage_and_exit()

    # Handle initialization flag
    if "--init" in sys.argv or "-init" in sys.argv:
        if not settings.CYBORGDB_API_KEY:
            logger.warning("No API key found. Please set the CYBORGDB_API_KEY environment variable if you want to install cyborgdb-core.")
        install_packages()
        print("CyborgDB packages installed successfully. You can now run the service.")
        sys.exit(0)

    # Ensure all required environment variables are set
    ensure_environment_variables()

    install_packages()

    # Check if service API key requirement is disabled
    if not settings.REQUIRE_API_KEY:
        logger.warning("API key requirement is disabled. This is not recommended for production environments.")

    port = settings.PORT
    # workers = os.cpu_count() * 2 + 1  # Recommended formula for CPU-bound workloads
    workers = 1  # Use single worker to avoid concurrency issues with index training  

    # Log startup information
    logger.info(f"Starting CyborgDB Service on port {port} with {workers} workers")
    logger.info(f"API documentation available at: http://localhost:{port}{settings.API_PREFIX}/docs")

    # Configure uvicorn parameters
    uvicorn_config = {
        "app": "cyborgdb_service.app:app",
        "host": "0.0.0.0",
        "port": port,
        "workers": workers,
        "reload": False
    }
    
    # Add SSL configuration if certificates are found
    if settings.is_https_enabled:
        uvicorn_config.update({
            "ssl_keyfile": settings.SSL_KEY_PATH,   
            "ssl_certfile": settings.SSL_CERT_PATH,
        })

    # Start the server
    uvicorn.run(**uvicorn_config)

if __name__ == "__main__":
    main()
import logging
import os
from pathlib import Path

def setup_logging():
    # Create logs directory in project root
    project_root = Path(__file__).parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_file = log_dir / "selenium_mcp.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file)),
            logging.StreamHandler()
        ]
    )
    
    # Return the logger
    return logging.getLogger(__name__)

# Create a global logger instance
logger = setup_logging()
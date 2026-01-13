# Core domain logic

import logging

# Configure logging for audit trail (T092)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create logger for core module
logger = logging.getLogger("acp_analyzer.core")

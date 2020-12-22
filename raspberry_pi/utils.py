"""
Universal classes and other non-static constructs.
"""
import os
import json
import logging.config
from .constants import LOG_CONFIG_PATH, LOG_DIR, LOGGER_NAME

# Configure logging and create a new logger instance
with open(LOG_CONFIG_PATH) as f:
    log_config = json.loads(f.read())
    handlers = log_config["handlers"]
    for handler in handlers:
        handler_config = handlers[handler]
        if "filename" in handler_config:
            handler_config["filename"] = os.path.join(LOG_DIR, handler_config["filename"])
logging.config.dictConfig(log_config)
logger = logging.getLogger(LOGGER_NAME)

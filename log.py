import logging
import threading

_LOGGER_INITIALIZED = False
_LOGGER_LOCK = threading.Lock()

def get_logger(name: str) -> logging.Logger:
    global _LOGGER_INITIALIZED
    
    with _LOGGER_LOCK:
        if not _LOGGER_INITIALIZED:
            # Set up handlers and formatters
            stream_handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]%(message)s')
            stream_handler.setFormatter(formatter)

            file_handler = logging.FileHandler("FileSense.log")
            file_handler.setFormatter(formatter)

            # Attach handlers to the root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(stream_handler)
            root_logger.addHandler(file_handler)
            root_logger.setLevel(logging.INFO)

            _LOGGER_INITIALIZED = True

    # Get and return the logger with the requested name
    return logging.getLogger(name)
import logging
import threading

_logger_initialized = False
_logger_lock = threading.Lock()

def get_logger(name: str) -> logging.Logger:
    global _logger_initialized
    
    with _logger_lock:
        if not _logger_initialized:
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

            _logger_initialized = True

    # Get and return the logger with the requested name
    return logging.getLogger(name)
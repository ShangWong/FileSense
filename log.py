import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    stream = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]%(message)s')
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    file = logging.FileHandler("FileSense.log")
    file.setFormatter(formatter)
    logger.addHandler(file)

    return logger
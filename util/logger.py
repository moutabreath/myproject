import logging
import logging.handlers

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    handler = logging.handlers.WatchedFileHandler("finq_ai.log")
    logger = logging.getLogger()
    formatter =logging.Formatter("%(asctime)s:%(name)s:%(levelname)s {%(module)s %(funcName)s}:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
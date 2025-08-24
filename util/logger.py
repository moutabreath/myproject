import logging


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("finq_ai")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
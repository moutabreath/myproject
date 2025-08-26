import logging
import logging.handlers
from pathlib import Path

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    log_path = "finq_ai.log"
    log_dir = Path(log_path).parent
    if log_dir and str(log_dir) != "":
        Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s {%(module)s %(funcName)s}:%(message)s")

    # Check for existing file handler for the target logfile
    file_handler_exists = False
    for h in logger.handlers:
        if isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) and Path(h.baseFilename).resolve() == Path(log_path).resolve():
            file_handler_exists = True
            break

    if not file_handler_exists:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Ensure only one console handler (StreamHandler to sys.stderr or sys.stdout)
    console_handler_exists = any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers)
    if not console_handler_exists:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
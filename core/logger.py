import logging
from logging.handlers import RotatingFileHandler
from config import LOG_FILE_PATH
from flask import current_app

def init_logger(app):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

def log_info(msg):
    if current_app:
        current_app.logger.info(f"[info] {msg}")
    else:
        logging.info(f"[info] {msg}")

def log_warning(msg):
    if current_app:
        current_app.logger.warning(f"[warning] {msg}")
    else:
        logging.warning(f"[warning] {msg}")

def log_error(msg):
    if current_app:
        current_app.logger.error(f"[error] {msg}")
    else:
        logging.error(f"[error] {msg}")

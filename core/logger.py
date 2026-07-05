"""日志模块 : 控制台 + 文件双输出，支持日志轮转"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import current_app

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FILE_PATH

def init_logger(app):
    """初始化 Flask 应用日志
    配置控制台和文件双输出：
    - 控制台：实时输出到终端
    - 文件：按大小轮转，保留5个备份（每个10MB）
    """
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(console_handler)

    # 创建日志目录（如果不存在）
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 文件输出（轮转，maxBytes=10MB，backupCount=5）
    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

def log_info(msg):
    """记录 information 级别日志"""
    if current_app:
        current_app.logger.info(f"[info] {msg}")
    else:
        logging.info(f"[info] {msg}")

def log_warning(msg):
    """记录 warning 级别日志"""
    if current_app:
        current_app.logger.warning(f"[warning] {msg}")
    else:
        logging.warning(f"[warning] {msg}")

def log_error(msg):
    """记录 error 级别日志"""
    if current_app:
        current_app.logger.error(f"[error] {msg}")
    else:
        logging.error(f"[error] {msg}")

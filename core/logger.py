"""
日志模块 - 控制台 + 文件双输出，支持日志轮转

负责管理应用程序的日志记录，提供统一的日志接口，支持控制台和文件双输出。

核心特性:
    - 控制台实时输出：方便开发调试和运维监控
    - 文件持久化存储：支持日志轮转，避免日志文件过大
    - 统一接口：提供 log_info, log_warning, log_error 三个便捷函数
    - 兼容模式：支持在 Flask 应用上下文内外使用

日志配置:
    - 日志级别: INFO(记录重要的运行信息)
    - 文件大小: 每个日志文件最大10MB
    - 备份数量: 保留最近5个日志文件
    - 日志路径: 从 config.LOG_FILE_PATH 获取，默认为 logs/webhook.log
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import current_app

# 添加项目根目录到 sys.path，确保能够导入 config 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOG_FILE_PATH


#初始化 Flask 应用日志系统
"""
    配置两个日志处理器：
        1. StreamHandler: 输出到控制台，实时显示日志
        2. RotatingFileHandler: 输出到文件，支持按大小轮转
"""
def init_logger(app):

    # 创建控制台处理器，输出到标准输出(stdout)
    console_handler = logging.StreamHandler()
    
    # 设置控制台日志格式：时间 - 级别 - 消息
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
   
    # 将控制台处理器添加到应用日志器
    app.logger.addHandler(console_handler)

    # 创建日志目录（如果不存在）
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 创建文件轮转处理器，输出到指定日志文件
    # maxBytes: 单个文件最大10MB，backupCount: 保留5个备份
    
    file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    # 将文件处理器添加到应用日志器
    app.logger.addHandler(file_handler)
    
    # 设置日志级别为 INFO，只记录 INFO 及以上级别的日志
    app.logger.setLevel(logging.INFO)

#记录 INFO 级别的日志
"""
    INFO 级别用于记录正常的运行信息
"""
def log_info(msg):

    if current_app:
        # 在 Flask 应用上下文内，使用应用的日志器
        current_app.logger.info(f"[info] {msg}")
    else:
        # 在应用上下文外，使用标准 logging 模块
        logging.info(f"[info] {msg}")

#记录 WARNING 级别的日志
"""
    WARNING 级别用于记录需要关注的异常情况，但不影响系统运行
"""
def log_warning(msg):
    
    if current_app:
        current_app.logger.warning(f"[warning] {msg}")
    else:
        logging.warning(f"[warning] {msg}")

#记录 ERROR 级别的日志
"""
    ERROR 级别用于记录严重的错误信息，可能影响系统功能
"""
def log_error(msg):
    
    if current_app:
        current_app.logger.error(f"[error] {msg}")
    else:
        logging.error(f"[error] {msg}")
"""数据库连接模块"""
import psycopg2
from config import DB_CONFIG
from core.logger import log_error

def get_db_connection():
    """获取 PostgreSQL 数据库连接"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        log_error(f"数据库连接失败: {e}")
        raise
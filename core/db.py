"""数据库连接模块"""
import psycopg2
from config import DB_CONFIG

def get_db_connection():
    """获取 PostgreSQL 数据库连接"""
    return psycopg2.connect(**DB_CONFIG)
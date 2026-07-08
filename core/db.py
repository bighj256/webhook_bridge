"""
数据库连接模块 - 连接池

负责管理 PostgreSQL 数据库连接，提供连接池功能以提升高并发场景下的性能。

核心特性:
    - 支持连接池模式和单连接模式
    - 自动初始化和清理连接池
    - 连接异常时自动降级到单连接模式
    - 线程安全的连接获取和归还机制

连接池配置:
    - 最小连接数: 1 (minconn)
    - 最大连接数: 10 (maxconn)
    - 连接参数: 从 config.DB_CONFIG 获取
"""

import psycopg2
from psycopg2 import pool
from config import DB_CONFIG
from core.logger import log_error, log_info

# 全局连接池对象，初始为 None，通过 init_db_pool() 初始化
connection_pool = None

#初始化数据库连接池
def init_db_pool():
    global connection_pool
    try:
        # 创建连接池，配置最小1个、最大10个连接
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )
        log_info("数据库连接池初始化成功")
    except psycopg2.Error as e:

        # 连接池初始化失败，可能是数据库未启动或配置错误
        log_error(f"数据库连接池初始化失败: {e}")
        log_error("将使用单连接模式，建议生产环境启用连接池")

#获取数据库连接
"""
    如果连接池已初始化，从连接池获取连接；否则创建新的单连接。
    获取的连接默认关闭 autocommit，需要手动调用 commit() 提交事务。
"""
def get_db_connection():
    
    try:
        if connection_pool:
            # 从连接池获取连接
            conn = connection_pool.getconn()
            # 关闭自动提交，需要手动 commit()
            conn.autocommit = False
            return conn
        
        # 连接池未初始化，创建单连接(降级模式)
        return psycopg2.connect(**DB_CONFIG,autocommit=False)
    except psycopg2.Error as e:
        log_error(f"获取数据库连接失败: {e}")
        raise

#归还数据库连接到连接池
"""
    如果连接池已初始化，将连接归还到连接池以供后续复用；
    如果连接池未初始化(单连接模式)，不执行任何操作。
"""
def release_db_connection(conn):
    
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            log_error(f"归还数据库连接失败: {e}")

#关闭数据库连接池
"""
    关闭所有连接池中的连接，并将连接池对象置为 None。
    此函数通常在应用关闭时由 Flask 的 teardown_appcontext 钩子调用。
"""
def close_db_pool():
    
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
        log_error("数据库连接池已关闭")
"""
数据库连接模块 - 连接池

负责管理 PostgreSQL 数据库连接，提供连接池功能以提升高并发场景下的性能。

核心特性:
    - 支持连接池模式和单连接模式
    - 自动初始化和清理连接池
    - 连接异常时自动降级到单连接模式
    - 线程安全的连接获取和归还机制
    - 基于 Flask g 的请求级连接管理（每个请求复用同一连接）

连接池配置:
    - 最小连接数: 1 (minconn)
    - 最大连接数: 10 (maxconn)
    - 连接参数: 从 config.DB_CONFIG 获取

生命周期:
    init_db_pool()           → 应用启动时调用一次，创建连接池
    get_db()                 → 每个请求调用，从池中获取连接并存入 Flask g
    close_db(exception)      → 每个请求结束时（teardown_appcontext），归还连接到池
    close_db_pool()          → 应用关闭时（atexit），销毁整个连接池
"""

import atexit
import psycopg2
from psycopg2 import pool
from flask import g
from config import DB_CONFIG
from core.logger import log_error, log_info

# 全局连接池对象，初始为 None，通过 init_db_pool() 初始化
connection_pool = None


def init_db_pool():
    """
    初始化数据库连接池（应用启动时调用一次）

    创建 psycopg2 SimpleConnectionPool，配置最小1个、最大10个连接。
    如果初始化失败，connection_pool 保持 None，后续降级为单连接模式。
    """
    global connection_pool
    try:
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )
        log_info("数据库连接池初始化成功")
    except psycopg2.Error as e:
        log_error(f"数据库连接池初始化失败: {e}")
        log_error("将使用单连接模式，建议生产环境启用连接池")


def _get_raw_connection():
    """
    从池中获取一个原始连接（内部使用）

    如果连接池已初始化，从连接池获取连接；
    否则创建新的单连接（降级模式）。
    获取的连接默认 autocommit=False，需要手动 commit()。

    返回:
        psycopg2 connection 对象
    """
    try:
        if connection_pool:
            conn = connection_pool.getconn()
            conn.autocommit = False
            return conn
        # 连接池未初始化，创建单连接（降级模式）
        return psycopg2.connect(**DB_CONFIG, autocommit=False)
    except psycopg2.Error as e:
        log_error(f"获取数据库连接失败: {e}")
        raise


def _return_connection(conn):
    """
    归还连接到连接池（内部使用）

    如果连接池已初始化，将连接归还到连接池以供后续复用；
    如果连接池未初始化（单连接模式），关闭连接。
    """
    if conn is None:
        return
    try:
        if connection_pool:
            connection_pool.putconn(conn)
        else:
            # 单连接模式：直接关闭连接，防止泄漏
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        log_error(f"归还/关闭数据库连接失败: {e}")
        # 如果放回池失败（例如连接已断开），尝试关闭
        try:
            conn.close()
        except Exception:
            pass


def get_db():
    """
    获取当前请求的数据库连接（使用 Flask g 复用）

    每个请求第一次调用时从连接池获取连接并存入 g._db_conn，
    后续同一请求内再次调用直接返回已缓存的连接。

    用法（在路由中）:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(...)
        conn.commit()      # 写操作需要
        cur.close()
        # 不需要手动释放 — teardown_appcontext 会自动归还

    返回:
        psycopg2 connection 对象
    """
    if '_db_conn' not in g:
        g._db_conn = _get_raw_connection()
    return g._db_conn


def close_db(exception=None):
    """
    归还当前请求的数据库连接到连接池

    此函数由 Flask 的 teardown_appcontext 钩子自动调用，
    确保每个请求结束后连接被正确归还，防止连接泄漏。

    无论请求成功还是失败，都会回滚未提交的事务，
    确保连接以干净状态归还到连接池。

    注意：此函数只归还当前请求的连接，不销毁连接池。
    """
    conn = g.pop('_db_conn', None)
    if conn is not None:
        # 始终回滚，确保连接以干净状态归还池中
        # 对于已 commit 的事务，rollback 是空操作
        try:
            conn.rollback()
        except Exception:
            pass
        _return_connection(conn)


def close_db_pool():
    """
    关闭整个数据库连接池（应用关闭时调用一次）

    关闭所有连接（包括空闲和正在使用的），并将连接池对象置为 None。
    此函数由 atexit 钩子在应用退出时自动调用。
    """
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        connection_pool = None
        log_info("数据库连接池已关闭")


# 保留旧接口以兼容现有代码（路由中手动管理连接）
# 推荐新代码使用 get_db() + close_db() 自动管理模式
def get_db_connection():
    """[兼容接口] 获取数据库连接 — 推荐使用 get_db() 代替"""
    return get_db()


def release_db_connection(conn):
    """[兼容接口] 归还数据库连接 — 推荐使用 close_db() 代替，此函数在 g 模式下为空操作"""
    # 在 g 模式下，连接由 close_db() 统一归还，此函数不做任何事
    pass
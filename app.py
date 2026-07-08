"""
Flask 主应用模块 - 智能农场 Webhook 服务器

本项目是智能农场系统的上位机后端，负责接收传感器数据并通过 Webhook 推送至 EMQX，
同时提供实时仪表盘和数据查询接口。

核心功能:
    - 数据接收: 通过 POST /api/sensor_data 接收 EMQX Webhook 转发的传感器数据
    - 实时推送: 通过 SSE (Server-Sent Events) 向前端推送实时数据更新
    - 数据查询: 提供 /api/latest、/api/stats、/api/trend 等数据查询接口
    - 用户认证: 提供 /auth/login、/auth/register 等认证接口
    - AI 助手: 提供 /api/ai/ask 接口，调用大模型生成农事建议

技术栈:
    - Flask: Web 框架
    - PostgreSQL: 数据库（通过连接池管理）
    - EMQX: MQTT Broker,通过 Webhook 推送数据
    - SSE: Server-Sent Events,用于实时数据推送

为什么需要这个功能:
    - 实现传感器数据的集中接收和存储
    - 提供实时监控仪表盘，方便用户随时查看环境数据
    - 集成 AI 农事助手，为农业生产提供智能决策支持
    - 支持数据导出和趋势分析，便于历史数据管理和研究

路由结构:
    /auth/*        - 认证相关路由（登录、注册、登出）
    /api/*         - API 接口（数据接收、查询、导出）
    /api/ai/*      - AI 农事助手接口
    /dashboard     - 仪表盘页面
    /health        - 健康检查接口

数据流向:
    传感器 → EMQX → /api/sensor_data → PostgreSQL → SSE → 前端仪表盘
"""
import atexit
from flask import Flask
from datetime import timedelta

from core.logger import init_logger
from core.db import init_db_pool, close_db, close_db_pool
from routes.api import api_bp
from routes.views import views_bp
from routes.auth import auth_bp
from routes.ai import ai_bp
from routes.middleware import register_middleware
from config import SECRET_KEY

app = Flask(__name__)

# 设置应用配置，会话加密密钥，用于防 CSRF 攻击
app.config['SECRET_KEY'] = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 初始化日志系统（控制台 + 文件双输出）
init_logger(app)

# 初始化数据库连接池（生产环境：连接池模式；降级方案：单连接模式）
# 连接池在整个应用生命周期内持续存在，不再每请求重建
init_db_pool()

# 注册应用退出时清理连接池（atexit 确保应用退出时执行一次）
atexit.register(close_db_pool)

# 注册蓝图
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(views_bp, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(ai_bp, url_prefix='/api/ai')

# 注册全局中间件（路由保护、登录状态检查等）
register_middleware(app)


@app.teardown_appcontext
def return_db_connection(exception=None):
    """
    Flask 请求结束后归还数据库连接到连接池

    每个请求结束时调用 close_db()，将当前请求使用的连接归还到连接池。
    如果有未提交的异常，会自动回滚事务。

    注意：这里归还的是单个连接，不是销毁整个连接池。
    连接池本身在应用退出时由 atexit 钩子负责关闭。
    """
    close_db(exception)


if __name__ == '__main__':
    """
    启动 Flask 开发服务器
    注意：
        - host='0.0.0.0': 监听所有网络接口，允许外部访问
        - port=5000: 监听 5000 端口
        - debug=False: 生产环境关闭调试模式（避免安全风险）
    """
    app.run(host='0.0.0.0', port=5000, debug=False)
"""
中间件模块

负责路由保护和全局请求处理，是系统安全的重要防线。

核心功能:
    - 首页重定向: 根据登录状态重定向到 Dashboard 或登录页面
    - 路由保护: 对受保护路径进行登录状态检查
    - Session管理: 设置会话为持久化状态

安全策略:
    - 白名单机制: 定义无需登录即可访问的路径列表
    - API保护: 未登录访问 API 返回 401 错误
    - 页面保护: 未登录访问页面重定向到登录页

允许访问的路径(白名单):
    - /                    - 首页
    - /auth/login          - 用户登录API
    - /auth/register       - 用户注册API
    - /auth/captcha        - 验证码获取
    - /auth/status         - 登录状态检查
    - /auth/login_page     - 登录页面
    - /auth/register_page  - 注册页面
    - /api/sensor_data     - 传感器数据接收(EMQX Webhook)
    - /health              - 健康检查

请求处理流程:
    1. 请求到达 → before_request 钩子触发
    2. 检查请求路径是否在白名单中
    3. 如果在白名单 → 直接放行
    4. 如果不在白名单 → 检查 Session 中是否有 user_id
    5. 已登录 → 放行
    6. 未登录 → API 返回 401，页面重定向到登录页
"""
from flask import session, redirect, url_for, request, jsonify


def register_middleware(app):
    """
    注册全局中间件
    
    将首页路由和 before_request 钩子注册到 Flask 应用实例。
    
    参数:
        app (Flask): Flask 应用实例
    
    注册的路由和钩子:
        - '/': 首页路由，根据登录状态重定向
        - before_request: 请求前钩子，进行路由保护检查
    """
    
    # ==============================================================================
    # 路由: GET /
    # 功能: 首页路由
    #根据用户登录状态进行重定向:
    #   - 已登录(user_id 在 Session 中): 重定向到 Dashboard
    #   - 未登录: 重定向到登录页面
    # ==============================================================================
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('views.dashboard'))
        return redirect(url_for('auth.login_page'))

    #请求前钩子 - 路由保护
    """
        在每个请求处理前执行，检查请求路径是否需要登录权限。
        对于受保护的路径，验证用户是否已登录。
        处理逻辑:
            1. 设置 Session 为持久化状态(有效期24小时)
            2. 检查路径是否在白名单中
            3. 对非白名单路径进行登录状态检查
            4. API 请求未登录返回 401
            5. 页面请求未登录重定向到登录页
    """
    @app.before_request
    def before_request():
        
        print(f"[DEBUG] request.path = {request.path}")
        
        # 白名单路径列表，无需登录即可访问
        allowed_paths = [
            '/',
            '/auth/login',
            '/auth/register',
            '/auth/captcha',
            '/auth/status',
            '/auth/login_page',
            '/auth/register_page',
            '/api/sensor_data',
            '/health'
        ]

        path = request.path
        # 设置会话为持久化，有效期由 PERMANENT_SESSION_LIFETIME 控制
        session.permanent = True

        # 白名单路径直接放行
        if path in allowed_paths:
                return

         # 检查是否为受保护路径(API 或 Dashboard)
        if path.startswith('/api/') or path == '/dashboard':
            # 验证登录状态
            if 'user_id' not in session:
                if path.startswith('/api/'):
                    return jsonify({"code": 401, "message": "请先登录"}), 401
               # 页面请求重定向到登录页
                return redirect(url_for('auth.login_page'))
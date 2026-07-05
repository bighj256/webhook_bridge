"""
中间件模块
负责路由保护和全局请求处理
"""
from flask import session, redirect, url_for, request, jsonify


def register_middleware(app):
    """
    注册全局中间件
    :param app: Flask 应用实例
    """
    
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('views.dashboard'))
        return redirect(url_for('auth.login_page'))

    @app.before_request
    def before_request():
        allowed_paths = [
            '/',
            '/auth/login',
            '/auth/register',
            '/auth/captcha',
            '/auth/status',
            '/auth/login_page',
            '/auth/register_page',
            '/health'
        ]
        
        path = request.path
        session.permanent = True
        
        if path.startswith('/api/') or path == '/dashboard':
            if 'user_id' not in session:
                if path.startswith('/api/'):
                    return jsonify({"code": 401, "message": "请先登录"}), 401
                return redirect(url_for('auth.login_page'))
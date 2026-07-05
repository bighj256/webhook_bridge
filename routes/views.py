"""
视图路由模块
负责页面渲染和健康检查等非 API 路由
"""
from flask import Blueprint, render_template, jsonify, redirect, url_for, session

# 创建视图蓝图，注册到 Flask 应用
views_bp = Blueprint('views', __name__)


# ==============================================================================
# 路由: GET /health
# 功能: 健康检查接口
# 用途: 服务状态监控、负载均衡探针、容器健康检查
# ==============================================================================
@views_bp.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


# ==============================================================================
# 路由: GET /dashboard
# 功能: 仪表盘页面
# 用途: 前端传感器数据可视化展示页面
# ==============================================================================
@views_bp.route('/dashboard')
def dashboard():
    """
    渲染仪表盘页面
    将当前登录用户信息传递给模板
    """
    return render_template('dashboard.html', username=session.get('username'))

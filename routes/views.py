"""
视图路由模块 - 页面渲染和健康检查

负责渲染前端页面(HTML)和提供健康检查接口,是系统的前端展示层。

核心功能:
    - 页面渲染: 提供 Dashboard 仪表盘、登录页、注册页等前端页面
    - 健康检查: 提供 /health 接口，用于服务状态监控和负载均衡探针
    - 页面跳转: 根据登录状态自动重定向到不同页面

技术说明:
    - 使用 Flask Blueprint 组织路由
    - 所有页面都通过 render_template() 渲染
    - 健康检查接口通常用于 Docker 容器健康检查

路由列表:
    GET /health      - 健康检查接口(返回 {"status": "ok"})
    GET /dashboard   - 仪表盘页面（显示传感器数据）

页面流程:
    1. 用户访问首页 / → middleware.before_request 检查登录状态
    2. 已登录 → 重定向到 /dashboard(仪表盘)
    3. 未登录 → 重定向到 /auth/login_page(登录页)
    4. 用户在页面内操作（查询数据、查看图表等）→ 前端异步请求 API
"""
from flask import Blueprint, render_template, jsonify, redirect, url_for, session

# 创建视图蓝图，注册到 Flask 应用
views_bp = Blueprint('views', __name__)


# ==============================================================================
# 路由: GET /health
# 功能: 健康检查接口
# 用于服务状态监控、负载均衡探针、容器健康检查等场景。
# 返回固定的 {"status": "ok"} 表示服务正常
# ==============================================================================
@views_bp.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


# ==============================================================================
# 路由: GET /dashboard
# 功能: 仪表盘页面
# 显示数据信息，以及AI助手
# ==============================================================================
@views_bp.route('/dashboard')
def dashboard():
    """
    页面加载流程:
        1. 前端加载 dashboard.html
        2. 建立 SSE 连接 /api/stream（实时数据推送）
        3. 发送请求获取最新数据 /api/latest
        4. 发送请求获取统计数据 /api/stats
        5. 发送请求获取趋势数据 /api/trend
        6. 前端渲染图表和仪表盘
    """
    return render_template('dashboard.html', username=session.get('username'))

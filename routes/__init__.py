"""
路由模块 - Flask 蓝图定义

包含所有的路由定义，按功能分组：
    - api.py: 传感器数据 API（接收、查询、导出、趋势）
    - auth.py: 用户认证 API（登录、注册、登出）
    - ai.py: AI 农事助手 API
    - middleware.py: 全局中间件
    - views.py: 页面渲染路由

所有路由通过 Flask Blueprint 组织，按前缀注册到主应用。
"""

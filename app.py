from flask import Flask
from core.logger import init_logger
from routes.api import api_bp
from routes.views import views_bp

app = Flask(__name__)

# 初始化日志配置
init_logger(app)

# 注册蓝图
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(views_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

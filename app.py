from flask import Flask
from core.logger import init_logger
from routes.api import api_bp
from routes.views import views_bp
from routes.auth import auth_bp
from routes.ai import ai_bp
from routes.middleware import register_middleware
from config import SECRET_KEY
from datetime import timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

init_logger(app)

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(views_bp, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(ai_bp, url_prefix='/api/ai')

register_middleware(app)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
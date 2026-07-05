from flask import Flask, session, redirect, url_for, request
from core.logger import init_logger
from routes.api import api_bp
from routes.views import views_bp
from routes.auth import auth_bp
from config import SECRET_KEY
from datetime import timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

init_logger(app)

@app.before_request
def before_request():
    allowed_paths = [
        '/auth/login',
        '/auth/register',
        '/auth/captcha',
        '/auth/status',
        '/views/health'
    ]
    
    path = request.path
    session.permanent = True
    
    if path.startswith('/api/') or path == '/views/dashboard':
        if 'user_id' not in session:
            if path.startswith('/api/'):
                from flask import jsonify
                return jsonify({"code": 401, "message": "请先登录"}), 401
            return redirect(url_for('auth.login_page'))

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(views_bp, url_prefix='/views')
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
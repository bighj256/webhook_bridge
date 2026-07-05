"""
认证路由模块
负责用户登录、注册、验证码生成和会话管理
"""
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, ImageDraw, ImageFont
import io
import random
import string

from core.logger import log_info, log_warning, log_error
from core.db import get_db_connection
from config import SECRET_KEY

auth_bp = Blueprint('auth', __name__)


def generate_captcha():
    """
    生成随机验证码图片
    返回: (验证码字符串, 图片字节流)
    """
    width, height = 120, 40
    chars = string.ascii_letters + string.digits
    captcha_text = ''.join(random.choices(chars, k=4))
    
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype('arial.ttf', 32)
    except:
        font = ImageFont.load_default()
    
    for i, char in enumerate(captcha_text):
        x = 15 + i * 25
        y = random.randint(2, 8)
        angle = random.randint(-15, 15)
        char_image = Image.new('RGBA', (25, 40), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((0, 0), char, font=font, fill=(0, 0, 0))
        char_image = char_image.rotate(angle, expand=True)
        image.paste(char_image, (x, y), char_image)
    
    for _ in range(15):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(128, 128, 128), width=1)
    
    for _ in range(30):
        x, y = random.randint(0, width), random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    
    return captcha_text, buf


# ==============================================================================
# 路由: GET /auth/captcha
# 功能: 获取验证码图片
# ==============================================================================
@auth_bp.route('/captcha')
def captcha():
    """
    获取验证码图片
    生成随机4位字母数字验证码，存储到 session 中，返回 PNG 图片
    """
    captcha_text, buf = generate_captcha()
    session['captcha'] = captcha_text.lower()
    session.permanent = True
    
    return buf.getvalue(), 200, {
        'Content-Type': 'image/png',
        'Cache-Control': 'no-cache, no-store, must-revalidate'
    }


# ==============================================================================
# 路由: POST /auth/login
# 功能: 用户登录
# ==============================================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    参数:
        username: 用户名
        password: 密码
        captcha: 验证码
    返回:
        200: {"code": 0, "message": "success"}
        400: {"code": 400, "message": "..."}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "No JSON data"}), 400
        
        username = data.get('username')
        password = data.get('password')
        captcha = data.get('captcha', '').lower()
        
        if not username or not password:
            return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400
        
        session_captcha = session.get('captcha', '')
        if captcha != session_captcha:
            return jsonify({"code": 400, "message": "验证码错误"}), 400
        session.pop('captcha', None)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            log_warning(f"Login failed: user {username} not found")
            return jsonify({"code": 400, "message": "用户名或密码错误"}), 400
        
        user_id, password_hash = row
        if not check_password_hash(password_hash, password):
            log_warning(f"Login failed: wrong password for user {username}")
            return jsonify({"code": 400, "message": "用户名或密码错误"}), 400
        
        session['user_id'] = user_id
        session['username'] = username
        log_info(f"User {username} logged in successfully")
        
        return jsonify({"code": 0, "message": "success"}), 200
    
    except Exception as e:
        log_error(f"Login error: {e}")
        return jsonify({"code": 500, "message": str(e)}), 500


# ==============================================================================
# 路由: POST /auth/register
# 功能: 用户注册
# ==============================================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    参数:
        username: 用户名
        password: 密码
        captcha: 验证码
    返回:
        200: {"code": 0, "message": "success"}
        400: {"code": 400, "message": "..."}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "No JSON data"}), 400
        
        username = data.get('username')
        password = data.get('password')
        captcha = data.get('captcha', '').lower()
        
        if not username or not password:
            return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400
        
        if len(username) < 3 or len(username) > 20:
            return jsonify({"code": 400, "message": "用户名长度需在3-20字符之间"}), 400
        
        if len(password) < 6:
            return jsonify({"code": 400, "message": "密码长度至少6位"}), 400
        
        session_captcha = session.get('captcha', '')
        if captcha != session_captcha:
            return jsonify({"code": 400, "message": "验证码错误"}), 400
        session.pop('captcha', None)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"code": 400, "message": "用户名已存在"}), 400
        
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
        
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        session['user_id'] = user_id
        session['username'] = username
        log_info(f"User {username} registered successfully")
        
        return jsonify({"code": 0, "message": "success"}), 200
    
    except Exception as e:
        log_error(f"Register error: {e}")
        return jsonify({"code": 500, "message": str(e)}), 500


# ==============================================================================
# 路由: POST /auth/logout
# 功能: 用户登出
# ==============================================================================
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户登出接口
    清空 session 中的用户信息
    """
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"code": 0, "message": "success"}), 200


# ==============================================================================
# 路由: GET /auth/login_page
# 功能: 渲染登录页面
# ==============================================================================
@auth_bp.route('/login_page')
def login_page():
    """
    渲染登录页面
    已登录用户直接重定向到仪表盘
    """
    if 'user_id' in session:
        return redirect(url_for('views.dashboard'))
    return render_template('login.html')


# ==============================================================================
# 路由: GET /auth/register_page
# 功能: 渲染注册页面
# ==============================================================================
@auth_bp.route('/register_page')
def register_page():
    """
    渲染注册页面
    已登录用户直接重定向到仪表盘
    """
    if 'user_id' in session:
        return redirect(url_for('views.dashboard'))
    return render_template('register.html')


# ==============================================================================
# 路由: GET /auth/status
# 功能: 获取登录状态
# ==============================================================================
@auth_bp.route('/status')
def status():
    """
    获取当前登录状态
    返回用户信息或未登录状态
    """
    if 'user_id' in session:
        return jsonify({
            "code": 0,
            "data": {
                "user_id": session['user_id'],
                "username": session['username']
            }
        })
    return jsonify({"code": 401, "message": "未登录"}), 401


# ==============================================================================
# 装饰器: login_required
# 功能: 路由保护，要求登录才能访问
# ==============================================================================
def login_required(f):
    """
    登录保护装饰器
    检查 session 中是否有 user_id，未登录则返回 401
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"code": 401, "message": "请先登录"}), 401
        return f(*args, **kwargs)
    
    return decorated_function
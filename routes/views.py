from flask import Blueprint, render_template, jsonify

views_bp = Blueprint('views', __name__)

@views_bp.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@views_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

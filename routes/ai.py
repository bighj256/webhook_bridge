"""
AI 农事助手路由模块
负责与 AI 模型交互，提供基于传感器数据的农事建议
"""
from flask import Blueprint, request, jsonify, session
import requests
import json
import traceback
import threading
from datetime import datetime

from core.logger import log_info, log_warning, log_error
from core.db import get_db_connection
from config import AI_CONFIG

ai_bp = Blueprint('ai', __name__)

SYSTEM_PROMPT = """
你是一名经验丰富的温室农业专家。请根据提供的实时环境数据，给出简洁、科学的农事操作建议。
你需要关注以下方面：
- 灌溉：根据土壤湿度判断是否需要浇水
- 通风：根据空气温度、湿度和CO₂浓度判断
- 遮阳/补光：根据光照强度判断
- 保温/降温：根据空气温度判断
- pH调节：根据土壤pH值判断是否需要施肥或调节
- 施肥：综合各项指标给出建议
要求：
- 使用中文，语言亲切专业
- 控制在200字以内
- 优先指出异常指标并给出具体操作建议
- 如果所有指标正常，给出保持建议
""".strip()

RANGES = {
    'temp': {'min': 18, 'max': 28, 'name': '空气温度', 'unit': '℃'},
    'air_humi': {'min': 45, 'max': 75, 'name': '空气湿度', 'unit': '%'},
    'soil_humi': {'min': 30, 'max': 70, 'name': '土壤湿度', 'unit': '%'},
    'light': {'min': 2000, 'max': 10000, 'name': '光照强度', 'unit': 'lux'},
    'ph': {'min': 6.0, 'max': 7.5, 'name': '土壤pH值', 'unit': ''},
    'co2': {'min': 400, 'max': 800, 'name': 'CO₂浓度', 'unit': 'ppm'}
}

# Per-user request locks to prevent concurrent AI calls from the same user
_user_locks = {}
_user_locks_lock = threading.Lock()


def _acquire_user_lock(user_id):
    """Try to acquire the per-user lock. Returns True if acquired, False if already held."""
    with _user_locks_lock:
        if user_id not in _user_locks:
            _user_locks[user_id] = threading.Lock()
        lock = _user_locks[user_id]
    return lock.acquire(blocking=False)


def _release_user_lock(user_id):
    """Release the per-user lock."""
    with _user_locks_lock:
        lock = _user_locks.get(user_id)
    if lock is not None and lock.locked():
        lock.release()


def get_status(value, key):
    if value is None:
        return '数据缺失'
    r = RANGES[key]
    if value < r['min']:
        return f'偏低（适宜范围 {r["min"]}{r["unit"]}~{r["max"]}{r["unit"]}）'
    elif value > r['max']:
        return f'偏高（适宜范围 {r["min"]}{r["unit"]}~{r["max"]}{r["unit"]}）'
    else:
        return f'正常（适宜范围 {r["min"]}{r["unit"]}~{r["max"]}{r["unit"]}）'


def format_sensor_data(data):
    """将传感器数据格式化为易读文本"""
    lines = []
    lines.append(f"📅 数据时间: {data['time']}")
    lines.append(f"\n📊 环境数据：")
    
    fields = ['temp', 'air_humi', 'soil_humi', 'light', 'ph', 'co2']
    for field in fields:
        value = data.get(field)
        r = RANGES[field]
        if value is not None:
            if isinstance(value, float):
                display_val = round(value, 1)
            else:
                display_val = value
            status = get_status(value, field)
            lines.append(f"- {r['name']}：{display_val}{r['unit']} 【{status}】")
        else:
            lines.append(f"- {r['name']}：数据缺失")
    
    return '\n'.join(lines)


def get_latest_sensor_data():
    """获取最新一条传感器数据"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT time, temp, air_humi, soil_humi, light, ph, co2
            FROM sensor_data
            ORDER BY time DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return None
        
        return {
            'time': row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temp': row[1],
            'air_humi': row[2],
            'soil_humi': row[3],
            'light': row[4],
            'ph': row[5],
            'co2': row[6]
        }
    except Exception as e:
        log_error(f"获取传感器数据失败: {e}")
        return None


def call_ai_api(messages):
    """调用 AI API"""
    api_key = AI_CONFIG['api_key']
    model_name = AI_CONFIG['model_name']
    api_base_url = AI_CONFIG['api_base_url']
    timeout = AI_CONFIG['timeout']
    
    if not api_key:
        return None, "未配置 AI API Key，请在 .env 文件中设置 AI_API_KEY"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'model': model_name,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 500,
        'stream': False,
        'thinking': {'type': 'disabled'}
    }
    
    try:
        url = f"{api_base_url}/chat/completions"
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']
            content = message.get('content')
            if content is not None and isinstance(content, str) and content.strip():
                return content.strip(), None

            # Zhipu AI thinking/reasoning mode may put the answer in reasoning_content
            reasoning = message.get('reasoning_content')
            if reasoning is not None and isinstance(reasoning, str) and reasoning.strip():
                return reasoning.strip(), None

            return None, "AI 返回内容为空，请重试"
        
        return None, "AI 返回格式异常"
    
    except requests.exceptions.Timeout:
        return None, "AI 请求超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        log_error(f"AI API 请求失败: {e}")
        return None, f"AI 请求失败: {str(e)}"
    except Exception as e:
        log_error(f"AI API 处理异常: {e}")
        log_error(traceback.format_exc())
        return None, "AI 服务异常，请稍后重试"


@ai_bp.route('/ask', methods=['POST'])
def ai_ask():
    """
    AI 农事助手接口
    请求体:
    {
        "question": "请问现在需要通风吗？",
        "history": []  // 可选，历史对话记录
    }
    返回:
    {
        "code": 0,
        "data": {
            "response": "AI回复内容",
            "sensor_data": {...}
        }
    }
    """
    try:
        # --- Per-user concurrency guard ---
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"code": 401, "message": "请先登录"}), 401

        if not _acquire_user_lock(user_id):
            return jsonify({
                "code": 429,
                "message": "您有一个正在处理中的 AI 请求，请等待完成后再试"
            }), 429

        try:
            data = request.get_json()
            if not data:
                return jsonify({"code": 400, "message": "No JSON data"}), 400

            question = data.get('question', '').strip()
            history = data.get('history', [])

            if len(question) > 500:
                return jsonify({"code": 400, "message": "问题长度不能超过500字符"}), 400

            sensor_data = get_latest_sensor_data()
            if not sensor_data:
                return jsonify({"code": 400, "message": "暂无传感器数据，请先等待数据上报"}), 400

            formatted_data = format_sensor_data(sensor_data)

            default_question = "请根据当前数据给出综合环境评估和农事建议"
            user_question = question if question else default_question

            user_prompt = f"""{formatted_data}

用户问题：{user_question}

请给出专业的农事建议："""

            messages = [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt}
            ]

            for h in history[-3:]:
                if h.get('role') and h.get('content'):
                    messages.append(h)

            response, error = call_ai_api(messages)

            if error:
                log_warning(f"AI 调用失败: {error}")
                return jsonify({"code": 500, "message": error}), 500

            log_info(f"AI 农事建议生成成功，问题: {user_question[:50]}...")

            return jsonify({
                "code": 0,
                "data": {
                    "response": response,
                    "sensor_data": sensor_data
                }
            })
        finally:
            _release_user_lock(user_id)

    except Exception as e:
        log_error(f"AI 接口异常: {e}")
        log_error(traceback.format_exc())
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@ai_bp.route('/status', methods=['GET'])
def ai_status():
    """检查 AI 配置状态"""
    api_key = AI_CONFIG['api_key']
    has_key = bool(api_key)
    return jsonify({
        "code": 0,
        "data": {
            "configured": has_key,
            "model": AI_CONFIG['model_name'],
            "base_url": AI_CONFIG['api_base_url']
        }
    })

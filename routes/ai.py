"""
AI 农事助手路由模块

负责与 AI 模型交互，提供基于传感器数据的农事建议，实现从"数据展示"到"智能决策辅助"的升级。

核心功能:
    - 智能分析: 获取实时传感器数据，调用大语言模型进行专业分析
    - 农事建议: 根据环境数据给出灌溉、通风、光照、温度调控等具体建议
    - 状态检查: 检查 AI API 配置状态，确保服务正常

AI 工作流程:
    1. 获取最新传感器数据（温度、湿度、光照、pH、CO₂等）
    2. 将数据格式化为自然语言文本
    3. 构造包含系统提示词、数据上下文和用户问题的完整 Prompt
    4. 调用外部 AI API（GLM-4.7-Flash）
    5. 返回 AI 生成的农事建议给前端

技术特性:
    - Prompt工程: 精心设计的系统提示词，定义角色和输出格式
    - 数据上下文: 将传感器数据转换为自然语言作为 AI 分析依据
    - 历史对话: 支持携带最近3条历史记录，保持对话连贯性
    - 参数限制: 用户问题长度限制≤500字符，防止滥用

路由列表:
    POST /api/ai/ask    - 咨询 AI 农事助手
    GET  /api/ai/status - 检查 AI 配置状态

配置要求:
    需要在 .env 文件中配置 AI_API_KEY、AI_MODEL_NAME、AI_API_BASE_URL
"""
from flask import Blueprint, request, jsonify, session
import requests
import json
import traceback
import threading
from datetime import datetime

from core.logger import log_info, log_warning, log_error
from core.db import get_db
from config import AI_CONFIG

ai_bp = Blueprint('ai', __name__)

# ==============================================================================
# SYSTEM_PROMPT - AI 系统提示词
# 功能: 定义 AI 的角色、任务和输出格式
# ==============================================================================
SYSTEM_PROMPT = """
你是一名经验丰富的温室农业专家，拥有20年以上的设施农业种植管理经验。请根据提供的实时环境数据，进行全面的环境评估并给出专业、具体、可操作的农事建议。

## 分析框架

你需要对每项指标逐一评估，并按以下结构输出报告：

### 一、环境数据总览
用表格列出所有指标的当前值、适宜范围、偏离程度（正常/偏低/偏高）。

### 二、异常指标逐项分析
对每个偏离适宜范围的指标，详细说明：
1. 当前数值与适宜范围的差距
2. 如果不处理可能导致的后果（如病害、减产、品质下降等）
3. 具体的、可量化的操作措施

### 三、综合农事操作建议

#### 🌊 灌溉管理
- 明确是否需要灌溉，需要的话给出建议浇水量（如"每平方米3-5升"）和浇水时段
- 说明判断依据（当前土壤湿度与作物需求的对比）

#### 💨 通风管理
- 是否需要通风，何时通风（如"上午10点至下午3点开启顶窗"）
- 通风时长和频次建议
- 结合温度、湿度、CO₂浓度综合判断

#### ☀️ 光照管理
- 判断光照是过强还是不足
- 补光方案：建议补光灯类型（LED植物灯/高压钠灯）、功率密度（W/m²）、每日补光时长
- 遮阳方案：遮阳率建议（如"使用50%遮阳网"）、开闭时段

#### 🌡️ 温度调控
- 升温措施：如覆盖地膜、开启加热设备、关闭通风口的时间
- 降温措施：如遮阳、通风、湿帘风机降温、喷雾降温
- 给出目标温度范围和调控时间节点

#### 🧪 土壤pH调节
- 当前pH对养分吸收的影响分析（如"pH偏高会导致铁、锰、锌等微量元素有效性降低"）
- 调酸方案：硫磺粉用量（如"每平方米施用50-80g硫磺粉"）、酸性肥料选择
- 调碱方案：石灰用量、施用方法
- 调节周期和后续监测建议

#### 🌱 施肥建议
- 根据各项指标和作物生长阶段推荐肥料种类和配比
- N-P-K 比例建议
- 施肥量和频次
- 有机肥与化肥的配合使用建议

### 四、风险预警
- 当前环境下可能发生的病虫害风险
- 预防措施建议
- 未来3-5天管理重点

## 输出要求
- 语言专业但通俗易懂，让普通农户也能理解执行
- 所有建议必须有具体数值，避免"适量""适当"等模糊表述
- 每项建议都要说明科学原理和预期效果
- 如果所有指标正常，简要说明当前管理得当之处并给出维持建议
""".strip()

# ==============================================================================
# RANGES - 传感器数据标准范围定义
# 功能: 定义各传感器指标的适宜范围，用于状态判断和提示
# ==============================================================================
RANGES = {
    'temp': {'min': 18, 'max': 28, 'name': '空气温度', 'unit': '℃'},          # 温度：18-28℃ 为适宜
    'air_humi': {'min': 45, 'max': 75, 'name': '空气湿度', 'unit': '%'},       # 空气湿度：45-75% 为适宜
    'soil_humi': {'min': 30, 'max': 70, 'name': '土壤湿度', 'unit': '%'},      # 土壤湿度：30-70% 为适宜
    'light': {'min': 2000, 'max': 10000, 'name': '光照强度', 'unit': 'lux'},   # 光照：2000-10000 lux 为适宜
    'ph': {'min': 6.0, 'max': 7.5, 'name': '土壤pH值', 'unit': ''},            # pH值：6.0-7.5 为适宜
    'co2': {'min': 400, 'max': 800, 'name': 'CO₂浓度', 'unit': 'ppm'}          # CO₂浓度：400-800 ppm 为适宜
}

# 每个用户的请求锁，以防止同一用户并发调用 AI
_user_locks = {}
_user_locks_lock = threading.Lock()

# 基于信号量的队列：容量等于 API 密钥数量，因此 N 个密钥 = N 个并发用户
# 其他请求在队列中等待；在配置加载后初始化
_slot_semaphore = None
_semaphore_lock = threading.Lock()


def _get_semaphore():
    """
    延迟初始化信号量

    懒加载信号量，容量等于 API 密钥数量，实现并发限制。
    N 个 API 密钥 = N 个并发槽位，其他请求需要排队等待。

    返回:
        threading.BoundedSemaphore: 信号量对象
    """
    global _slot_semaphore
    if _slot_semaphore is None:
        with _semaphore_lock:
            if _slot_semaphore is None:
                # 并发限制：每个 API 密钥支持一个并发请求
                # 如果没有配置密钥，至少保留 1 个槽位（防止阻塞）
                num_keys = len(AI_CONFIG['api_keys'])
                _slot_semaphore = threading.BoundedSemaphore(max(1, num_keys))
    return _slot_semaphore


def _acquire_user_lock(user_id):
    """
    获取用户级别的锁
    防止同一用户同时发送多个 AI 请求，避免资源浪费和 API 配额超限。

    返回:
        bool: True 表示成功获取锁，False 表示锁已被占用
    """
    with _user_locks_lock:
        # 如果用户锁不存在，创建一个新的锁
        if user_id not in _user_locks:
            _user_locks[user_id] = threading.Lock()
        lock = _user_locks[user_id]
    # 非阻塞获取锁，立即返回结果
    return lock.acquire(blocking=False)


def _release_user_lock(user_id):
    """
    释放用户级别的锁
    """
    with _user_locks_lock:
        lock = _user_locks.get(user_id)
    if lock is not None and lock.locked():
        lock.release()


def get_status(value, key):
    """
    获取传感器数据状态
    根据传感器值和标准范围判断数据状态：偏低、正常或偏高。

    参数:
        value: 传感器数值
        key: 传感器字段名（用于查找对应的范围定义）

    返回:
        str: 状态描述字符串，如"正常（适宜范围 18℃~28℃）"
    """
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
    """
    将传感器数据格式化为易读的自然语言文本
    将传感器数值转换为用户友好的格式，包括时间戳、各指标数值和状态。
    """
    lines = []
    lines.append(f"📅 数据时间: {data['time']}")
    lines.append(f"\n📊 环境数据：")

    # 遍历所有传感器字段
    fields = ['temp', 'air_humi', 'soil_humi', 'light', 'ph', 'co2']
    for field in fields:
        value = data.get(field)
        r = RANGES[field]
        if value is not None:
            # 浮点数保留1位小数
            if isinstance(value, float):
                display_val = round(value, 1)
            else:
                display_val = value
            # 获取状态并添加到输出
            status = get_status(value, field)
            lines.append(f"- {r['name']}：{display_val}{r['unit']} 【{status}】")
        else:
            lines.append(f"- {r['name']}：数据缺失")

    return '\n'.join(lines)


def get_latest_sensor_data():
    """
    获取最新一条传感器数据
    从数据库查询时间戳最新的一条传感器记录，用于 AI 分析。

    返回:
        dict or None: 包含最新传感器数据的字典，格式为：
                     {
                         'time': datetime对象,
                         'temp': 浮点数,
                         'air_humi': 浮点数,
                         'soil_humi': 浮点数,
                         'light': 浮点数,
                         'ph': 浮点数,
                         'co2': 浮点数
                     }
                     如果数据库中没有数据，返回 None
    """
    try:
        conn = get_db()
        cur = conn.cursor()

        # 查询最新一条数据（按时间倒序，取第一条）
        cur.execute("""
            SELECT time, temp, air_humi, soil_humi, light, ph, co2
            FROM sensor_data
            ORDER BY time DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()

        # 处理无数据情况
        if not row:
            return None

        # 构造返回数据，时间转换为可读格式
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
        # 记录错误并返回 None
        log_error(f"获取传感器数据失败: {e}")
        return None


# 用于 API 密钥选择的轮询计数器（通过锁保证线程安全)
_key_counter = 0
_key_counter_lock = threading.Lock()


def _get_next_api_key():
    """
    轮询选择下一个 API 密钥
    使用轮询算法分配 API 密钥，实现请求的负载均衡。
    每次调用返回不同的密钥，直到所有密钥都被使用一次。

    返回:
        str: 选中的 API 密钥，如果未配置则返回空字符串
    """
    global _key_counter
    keys = AI_CONFIG['api_keys']
    if not keys:
        return ""
    with _key_counter_lock:
        # 使用取模运算选择密钥，实现轮询
        key = keys[_key_counter % len(keys)]
        _key_counter += 1
    return key


def call_ai_api(messages):
    """
    调用 AI API
    向大语言模型发送请求，获取农事建议。

    错误处理:
        - API 配置错误：返回 "未配置 AI API Key..."
        - 超时：返回 "AI 请求超时..."
        - 请求失败：返回具体错误信息
        - 格式异常：返回 "AI 返回格式异常" 或 "AI 返回内容为空..."
    """
    api_keys = AI_CONFIG['api_keys']
    model_name = AI_CONFIG['model_name']
    api_base_url = AI_CONFIG['api_base_url']
    timeout = AI_CONFIG['timeout']

    # 检查是否配置了 API 密钥
    if not api_keys:
        return None, "未配置 AI API Key,请在 .env 文件中设置 AI_API_KEY"

    # 使用轮询算法选择密钥
    api_key = _get_next_api_key()
    # 记录当前使用的密钥索引（从 1 开始，便于日志显示）
    api_key_index = api_keys.index(api_key) + 1 if api_key in api_keys else 0
    log_info(f"Using API key #{api_key_index}/{len(api_keys)}")

    # ==============================================================================
    # 构建 API 请求 Payload
    # 功能: 构造符合 OpenAI 格式的请求体
    # ==============================================================================
    payload = {
        'model': model_name,
        'messages': messages,
        'temperature': 0.7,  # 控制生成随机性（0.0-1.0）
        'max_tokens': 2000    # 最大生成token数
    }

    try:
        # ==============================================================================
        # API 请求发送
        # 功能: 发送 POST 请求到大模型 API
        # ==============================================================================
        url = f"{api_base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        # timeout=(10, timeout): 连接超时 10 秒，读取超时 timeout 秒
        response = requests.post(url, headers=headers, json=payload, timeout=(10, timeout))
        response.raise_for_status()

        # ==============================================================================
        # 解析 API 响应
        # 功能: 从响应中提取 AI 生成的内容
        # ==============================================================================
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            message = result['choices'][0]['message']
            # 优先提取 content 字段
            content = message.get('content')
            if content is not None and isinstance(content, str) and content.strip():
                return content.strip(), None

            # 智谱 AI 思考/推理模式将答案放在 reasoning_content 字段中
            # 兼容思考模式（将思考过程作为答案返回）
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

# ==============================================================================
# 路由: POST /api/ai/ask
# 功能: AI 农事助手接口
# ==============================================================================
@ai_bp.route('/ask', methods=['POST'])
def ai_ask():
    """
    AI 农事助手接口
    用户提交问题时，系统调用大语言模型，根据当前传感器数据生成专业的农事建议。

    请求体格式:
    {
        "question": "请问现在需要通风吗？"    // 用户问题（可选，默认询问综合建议）
        "history": []  // 可选,历史对话记录(最多保留3条)
    }

    返回格式:
    {
        "code": 0,                    // 0=成功
        "data": {
            "response": "AI回复内容...",  // 农事建议
            "sensor_data": {...}        // 传感器数据快照
        }
    }

    错误码说明:
        401: 未登录
        429: 用户有未完成的 AI 请求
        400: 请求参数错误（问题超长、无数据等）
        202: 正在排队（API 并发槽位已满）
        500: 服务器错误

    并发控制:
        1. Per-user 锁：同一用户只能有一个活跃请求
        2. Semaphore：限制并发请求数 = API 密钥数量
    """
    try:
        # ==============================================================================
        # Per-user 并发控制：登录检查
        # 功能: 确保用户已登录才能使用 AI 功能
        # ==============================================================================
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"code": 401, "message": "请先登录"}), 401

        # ==============================================================================
        # Per-user 并发控制：用户锁获取
        # 功能: 防止同一用户同时发送多个请求
        # ==============================================================================
        if not _acquire_user_lock(user_id):
            return jsonify({
                "code": 429,
                "message": "您有一个正在处理中的 AI 请求，请等待完成后再试"
            }), 429

        try:
            # ==============================================================================
            # 解析请求参数
            # ==============================================================================
            data = request.get_json()
            if not data:
                return jsonify({"code": 400, "message": "No JSON data"}), 400

            question = data.get('question', '').strip()
            history = data.get('history', [])

            # 参数校验：问题长度限制
            if len(question) > 500:
                return jsonify({"code": 400, "message": "问题长度不能超过500字符"}), 400

            # ==============================================================================
            # 获取传感器数据
            # ==============================================================================
            sensor_data = get_latest_sensor_data()
            if not sensor_data:
                return jsonify({"code": 400, "message": "暂无传感器数据，请先等待数据上报"}), 400

            # ==============================================================================
            # 格式化数据为自然语言
            # ==============================================================================
            formatted_data = format_sensor_data(sensor_data)

            # 默认问题：如果用户未提供，使用综合建议提示
            default_question = "请根据当前数据给出综合环境评估和农事建议"
            user_question = question if question else default_question

            # ==============================================================================
            # 构造用户 Prompt
            # ==============================================================================
            user_prompt = f"""{formatted_data}

用户问题：{user_question}

请给出专业的农事建议："""

            # ==============================================================================
            # 构造消息列表
            # ==============================================================================
            messages = [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt}
            ]

            # 添加历史对话记录（最多3条）
            for h in history[-3:]:
                if h.get('role') and h.get('content'):
                    messages.append(h)

            # ==============================================================================
            # Semaphore 并发控制：获取槽位
            # ==============================================================================
            sem = _get_semaphore()
            acquired = sem.acquire(blocking=False)
            if not acquired:
                return jsonify({
                    "code": 202,
                    "message": "当前访问人数过多，正在排队等待中，请稍后重试..."
                }), 202

            try:
                # ==============================================================================
                # 调用 AI API
                # ==============================================================================
                response, error = call_ai_api(messages)
            finally:
                # 无论成功或失败，都释放槽位
                sem.release()

            # ==============================================================================
            # 处理错误情况
            # ==============================================================================
            if error:
                log_warning(f"AI 调用失败: {error}")
                return jsonify({"code": 500, "message": error}), 500

            log_info(f"AI 农事建议生成成功，问题: {user_question[:50]}...")

            # ==============================================================================
            # 返回成功响应
            # ==============================================================================
            return jsonify({
                "code": 0,
                "data": {
                    "response": response,
                    "sensor_data": sensor_data
                }
            })
        finally:
            # ==============================================================================
            # 释放用户锁
            # ==============================================================================
            _release_user_lock(user_id)

    except Exception as e:
        log_error(f"AI 接口异常: {e}")
        log_error(traceback.format_exc())
        return jsonify({"code": 500, "message": "服务器内部错误"}), 500


# ==============================================================================
# 路由: GET /api/ai/status
# 功能: 检查 AI 配置状态
# ==============================================================================
@ai_bp.route('/status', methods=['GET'])
def ai_status():
    """
    检查 AI 配置状态
    返回当前 AI 服务的配置信息，用于前端显示服务可用性和配置参数。

    返回格式:
    {
        "code": 0,
        "data": {
            "configured": true/false,  // 是否配置了 API 密钥
            "model": "glm-4.7-flash",   // 使用的模型名称
            "base_url": "https://..."   // API 基础地址
        }
    }

    用途:
        - 前端显示 AI 服务是否可用
        - 配置错误时提示用户
        - 显示当前使用的模型和 API 地址
    """
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

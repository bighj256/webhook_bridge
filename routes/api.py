"""
API 路由模块
负责传感器数据的接收、存储、查询、导出和实时推送
"""
from flask import Blueprint, request, jsonify, Response
import json
import traceback
import queue
import csv
import io
import psycopg2
from datetime import datetime, timedelta

from core.logger import log_info, log_warning, log_error
from core.db import get_db_connection
from core.sse import add_sse_client, remove_sse_client, broadcast_sse, sse_clients

# 创建 API 蓝图，注册到 Flask 应用
api_bp = Blueprint('api', __name__)


# ==============================================================================
# 路由: POST /api/sensor_data
# 功能: 接收 EMQX Webhook 转发的传感器数据，入库并广播
# 来源: EMQX 配置的 Webhook 触发
# ==============================================================================
@api_bp.route('/sensor_data', methods=['POST'])
def handle_sensor_data():
    """
    处理传感器数据接收请求
    流程:
    1. 解析请求中的 JSON 数据
    2. 处理 EMQX 嵌套的 payload 结构（支持字符串和对象两种格式）
    3. 提取并校验传感器字段
    4. 将数据插入 PostgreSQL 数据库
    5. 通过 SSE 广播给所有在线客户端
    请求格式:
    {
        "temp": 25.3,          // 温度
        "air_humi": 65.2,      // 空气湿度
        "soil_humi": 45.8,     // 土壤湿度
        "light": 5200,         // 光照强度
        "ph": 6.5,             // pH值
        "co2": 580,            // CO2浓度
        "time": 1715000000     // Unix时间戳（必填）
    }
    或 EMQX 嵌套格式:
    {
        "payload": "{\"temp\":25.3,...}"  // JSON字符串格式
        或
        "payload": {"temp":25.3,...}      // JSON对象格式
    }
    返回:
        200: {"code": 0, "message": "success"}
        400: {"code": 400, "message": "..."}
        500: {"code": 500, "message": "..."}
    """
    try:
        # 获取请求体中的 JSON 数据
        data = request.get_json()
        
        # 校验 JSON 数据是否存在
        if not data:
            log_warning("Received request without JSON data")
            return jsonify({"code": 400, "message": "No JSON data"}), 400

        # 记录收到的原始数据（限制长度避免日志过大）
        raw_data_str = json.dumps(data, ensure_ascii=False)[:500]
        log_info(f"Received raw data: {raw_data_str}")

        # 处理 EMQX Webhook 的嵌套 payload 结构
        # EMQX 转发时可能将实际数据放在 payload 字段中
        payload = data
        if 'payload' in data:
            payload_str = data['payload']
            # 如果 payload 是字符串，需要解析为 JSON 对象
            if isinstance(payload_str, str):
                try:
                    payload = json.loads(payload_str)
                    log_info(f"Decoded payload from string: {json.dumps(payload, ensure_ascii=False)[:500]}")
                except json.JSONDecodeError as e:
                    log_error(f"Failed to decode payload JSON: {e}, raw payload string: {payload_str[:200]}")
                    return jsonify({"code": 400, "message": "Invalid payload JSON"}), 400
            else:
                # payload 已经是对象，直接使用
                payload = payload_str

        # 从 payload 中提取各个传感器字段
        temp = payload.get('temp')           # 温度
        air_humi = payload.get('air_humi')   # 空气湿度
        soil_humi = payload.get('soil_humi') # 土壤湿度
        light = payload.get('light')         # 光照强度
        ph = payload.get('ph')               # pH值
        co2 = payload.get('co2')             # CO2浓度
        timestamp_unix = payload.get('time') # Unix时间戳（必填）

        # 记录提取到的数据（便于追踪插入失败时的数据）
        extracted_data = {
            'temp': temp,
            'air_humi': air_humi,
            'soil_humi': soil_humi,
            'light': light,
            'ph': ph,
            'co2': co2,
            'time': timestamp_unix
        }
        log_info(f"Extracted fields: {extracted_data}")

        # 校验时间戳字段是否存在
        if timestamp_unix is None:
            log_warning("Missing 'time' field in payload, cannot insert")
            return jsonify({"code": 400, "message": "Missing 'time' field"}), 400

        # 连接数据库并插入数据
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL 插入语句：将 Unix 时间戳转换为 PostgreSQL 时间类型
        insert_sql = """
            INSERT INTO sensor_data (time, temp, air_humi, soil_humi, light, ph, co2)
            VALUES (to_timestamp(%s), %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp_unix, temp, air_humi, soil_humi, light, ph, co2)
        cur.execute(insert_sql, params)
        conn.commit()
        
        # 关闭数据库连接
        cur.close()
        conn.close()

        # 推送新数据到所有在线的 SSE 客户端（实时更新前端）
        push_data = {
            'time': datetime.fromtimestamp(timestamp_unix).isoformat() if timestamp_unix else datetime.now().isoformat(),
            'temp': temp,
            'air_humi': air_humi,
            'soil_humi': soil_humi,
            'light': light,
            'ph': ph,
            'co2': co2
        }
        push_str = json.dumps(push_data, ensure_ascii=False)
        broadcast_sse(push_str)

        # 记录成功日志
        log_info(f"Data inserted successfully: temp={temp}, air_humi={air_humi}, time={timestamp_unix}")
        return jsonify({"code": 0, "message": "success"}), 200

    except psycopg2.Error as e:
        # 数据库错误处理（约束违反、类型错误等）
        log_error(f"Database error while inserting: {e}")
        if 'params' in locals():
            log_error(f"SQL parameters that caused error: {params}")
        else:
            log_error("Could not capture SQL parameters due to earlier exception.")
        log_error(traceback.format_exc())
        return jsonify({"code": 500, "message": f"Database error: {str(e)}"}), 500

    except Exception as e:
        # 其他未知错误处理
        log_error(f"Unexpected error: {e}")
        log_error(traceback.format_exc())
        return jsonify({"code": 500, "message": str(e)}), 500


# ==============================================================================
# 路由: GET /api/stream
# 功能: SSE (Server-Sent Events) 实时数据流接口
# 用途: 前端仪表盘实时接收传感器数据更新
# ==============================================================================
@api_bp.route('/stream')
def stream():
    """
    SSE 实时数据流接口
    
    前端通过 EventSource 连接此接口，实现服务器主动推送
    当有新数据插入时，通过 broadcast_sse() 推送给所有客户端
    
    返回:
        text/event-stream 格式的 SSE 数据流
    """
    def event_stream():
        # 创建客户端消息队列（最大缓存10条）
        q = queue.Queue(maxsize=10)
        
        # 将客户端队列注册到 SSE 客户端列表
        add_sse_client(q)
        
        try:
            # 持续阻塞等待新数据
            while True:
                # 从队列获取数据（阻塞直到有数据）
                data = q.get()
                # 按 SSE 格式输出（data: xxx\n\n）
                yield f"data: {data}\n\n"
        except GeneratorExit:
            # 客户端断开连接时，移除队列
            remove_sse_client(q)

    # 返回 SSE 响应，声明内容类型为 text/event-stream
    return Response(event_stream(), mimetype="text/event-stream")


# ==============================================================================
# 路由: GET /api/latest
# 功能: 获取最新一条传感器数据
# 用途: 前端仪表盘卡片展示当前数值
# ==============================================================================
@api_bp.route('/latest')
def latest_data():
    """
    获取最新一条传感器数据
    查询 sensor_data 表中时间最晚的一条记录，用于前端仪表盘卡片展示
    返回:
        200: {time, temp, air_humi, soil_humi, light, ph, co2}
        404: {"error": "no data"}
        500: {"error": "..."}
    """
    try:
        # 连接数据库
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 查询最新一条数据（按时间倒序，取第一条）
        cur.execute("""
            SELECT time, temp, air_humi, soil_humi, light, ph, co2
            FROM sensor_data
            ORDER BY time DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        
        # 关闭数据库连接
        cur.close()
        conn.close()

        # 处理无数据情况
        if not row:
            log_warning("No data found in sensor_data table")
            return jsonify({"error": "no data"}), 404

        # 构造返回数据，将时间转换为 ISO 格式
        return jsonify({
            'time': row[0].isoformat() if row[0] else None,
            'temp': row[1],
            'air_humi': row[2],
            'soil_humi': row[3],
            'light': row[4],
            'ph': row[5],
            'co2': row[6]
        })
    except Exception as e:
        # 错误处理
        log_error(f"Error in /latest: {e}")
        log_error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# 路由: GET /api/stats
# 功能: 获取最近24小时聚合统计数据
# 用途: 前端展示各指标的均值、最大值、最小值
# ==============================================================================
@api_bp.route('/stats')
def get_stats():
    """
    获取最近24小时聚合统计数据
    对每个传感器指标计算：平均值、最大值、最小值
    返回:
        {
            "temp": {"avg": 25.5, "max": 32.1, "min": 18.3},
            "air_humi": {"avg": 60.0, "max": 70.0, "min": 50.0},
            ...
        }
    """
    try:
        # 连接数据库
        conn = get_db_connection()
        cur = conn.cursor()
        
        # SQL 查询：计算最近24小时各指标的统计值
        sql = """
            SELECT 
                AVG(temp), MAX(temp), MIN(temp),
                AVG(air_humi), MAX(air_humi), MIN(air_humi),
                AVG(soil_humi), MAX(soil_humi), MIN(soil_humi),
                AVG(light), MAX(light), MIN(light),
                AVG(ph), MAX(ph), MIN(ph),
                AVG(co2), MAX(co2), MIN(co2)
            FROM sensor_data
            WHERE time >= NOW() - INTERVAL '24 hours'
        """
        cur.execute(sql)
        row = cur.fetchone()
        
        # 关闭数据库连接
        cur.close()
        conn.close()
        
        # 处理无数据情况
        if not row or row[0] is None:
            return jsonify({})
            
        # 构造统计结果字典，保留1位小数
        stats = {
            'temp': {'avg': round(float(row[0]), 1), 'max': round(float(row[1]), 1), 'min': round(float(row[2]), 1)},
            'air_humi': {'avg': round(float(row[3]), 1), 'max': round(float(row[4]), 1), 'min': round(float(row[5]), 1)},
            'soil_humi': {'avg': round(float(row[6]), 1), 'max': round(float(row[7]), 1), 'min': round(float(row[8]), 1)},
            'light': {'avg': round(float(row[9]), 1), 'max': round(float(row[10]), 1), 'min': round(float(row[11]), 1)},
            'ph': {'avg': round(float(row[12]), 1), 'max': round(float(row[13]), 1), 'min': round(float(row[14]), 1)},
            'co2': {'avg': round(float(row[15]), 1), 'max': round(float(row[16]), 1), 'min': round(float(row[17]), 1)}
        }
        return jsonify(stats)
    except Exception as e:
        # 错误处理
        log_error(f"Error in /stats: {e}")
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# 路由: GET /api/export
# 功能: 导出传感器数据为 CSV 文件
# 用途: 数据备份和离线分析
# ==============================================================================
@api_bp.route('/export')
def export_data():
    """
    导出传感器数据为 CSV 文件
    查询参数:
        start: 开始时间（可选，格式: YYYY-MM-DD HH:MM:SS）
        end: 结束时间（可选，格式: YYYY-MM-DD HH:MM:SS）
        params: 要导出的字段，逗号分隔（默认: temp）
                可选值: ph, co2, soil_humi, light, temp, air_humi
    返回:
        CSV 文件下载（Content-Disposition: attachment）
    """
    # 获取查询参数
    start_str = request.args.get('start')     # 开始时间
    end_str = request.args.get('end')         # 结束时间
    params_str = request.args.get('params', 'temp')  # 导出字段
    
    # 校验并过滤允许的字段（防止 SQL 注入）
    allowed_fields = ['ph', 'co2', 'soil_humi', 'light', 'temp', 'air_humi']
    fields = [f.strip() for f in params_str.split(',') if f.strip() in allowed_fields]
    
    # 如果没有合法字段，返回错误
    if not fields:
        return jsonify({'error': 'invalid params'}), 400
        
    try:
        # 连接数据库
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 动态构建 SQL 查询语句
        query = f"SELECT time, {', '.join(fields)} FROM sensor_data "
        sql_params = []
        conditions = []
        
        # 添加时间范围条件（如果提供）
        if start_str:
            conditions.append("time >= %s")
            sql_params.append(start_str)
        if end_str:
            conditions.append("time <= %s")
            sql_params.append(end_str)
            
        # 拼接 WHERE 子句
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        # 添加排序和限制（最多导出10000条）
        query += " ORDER BY time DESC LIMIT 10000"
        
        # 执行查询
        cur.execute(query, tuple(sql_params))
        rows = cur.fetchall()
        
        # 关闭数据库连接
        cur.close()
        conn.close()
        
        # 使用 StringIO 构建 CSV 内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入 CSV 表头
        writer.writerow(['Time'] + fields)
        
        # 写入数据行
        for row in rows:
            # 将时间格式化为可读字符串
            writer.writerow([row[0].strftime('%Y-%m-%d %H:%M:%S')] + list(row[1:]))
            
        # 返回 CSV 文件下载响应
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=sensor_data.csv"}
        )
    except Exception as e:
        # 错误处理
        log_error(f"Error in /export: {e}")
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# 路由: GET /api/trend
# 功能: 获取历史趋势数据（支持多种时间粒度）
# 用途: 前端图表展示数据随时间变化的趋势
# ==============================================================================
@api_bp.route('/trend')
def trend_data():
    """
    获取历史趋势数据
    查询参数:
        params: 要查询的字段，逗号分隔（默认: temp，最多2个）
                可选值: ph, co2, soil_humi, light, temp, air_humi
        unit: 时间粒度（默认: hour）
              可选值: 30m, 1h, 6h, 12h, hour, day, week, month, year, live
        start: 自定义开始时间（可选）
        end: 自定义结束时间（可选）
    返回:
        {
            "labels": ["2024-01-01 00:00", ...],  // 时间标签
            "full_labels": [...],                 // 完整时间标签
            "datasets": {                         // 各字段数据
                "temp": [25.3, 25.5, ...],
                "air_humi": [65.2, 64.8, ...]
            }
        }
    """
    # 获取查询参数
    params_str = request.args.get('params', 'temp')  # 查询字段
    unit = request.args.get('unit', 'hour')         # 时间粒度
    start_str = request.args.get('start')           # 自定义开始时间
    end_str = request.args.get('end')               # 自定义结束时间
    
    # 校验并过滤允许的字段（最多2个，防止查询过慢）
    allowed_fields = ['ph', 'co2', 'soil_humi', 'light', 'temp', 'air_humi']
    fields = [f.strip() for f in params_str.split(',') if f.strip() in allowed_fields][:2]
    
    # 如果没有合法字段，返回错误
    if not fields:
        return jsonify({'error': 'invalid params'}), 400

    # 实时模式：直接获取最近60条原始数据
    if unit == 'live':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # 查询最近60条数据
            sql = f"SELECT time, {', '.join(fields)} FROM sensor_data ORDER BY time DESC LIMIT 60"
            cur.execute(sql)
            rows = cur.fetchall()
            
            cur.close()
            conn.close()
            
            # 反转数据（按时间正序）
            rows.reverse()
            
            # 构造返回数据
            labels = []
            full_labels = []
            datasets = {f: [] for f in fields}
            
            for row in rows:
                t = row[0]
                time_str = t.strftime('%Y-%m-%d %H:%M')
                labels.append(time_str)
                full_labels.append(time_str)
                
                # 填充各字段数据
                for idx, f in enumerate(fields):
                    val = row[idx + 1]
                    datasets[f].append(round(float(val), 2) if val is not None else None)
            
            return jsonify({'labels': labels, 'full_labels': full_labels, 'datasets': datasets})
        except Exception as e:
            log_error(f"Error in /trend live: {e}")
            return jsonify({'error': str(e)}), 500

    # 非实时模式：按时间桶聚合
    now = datetime.now()
    
    # 处理自定义时间范围
    if start_str:
        try:
            # 解析时间字符串（兼容多种格式）
            def parse_dt(s):
                # 移除时区信息，统一处理
                s = s.replace('Z', '').split('+')[0].replace('T', ' ').split('.')[0]
                # 如果只有16位（缺少秒），补全秒
                if len(s) == 16:
                    s += ':00'
                return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

            start_date = parse_dt(start_str)
            end_date = parse_dt(end_str) if end_str else now
            
            # 根据时间跨度自动选择粒度
            delta = end_date - start_date
            if delta.days > 60:
                grain = 'day'
                db_interval = '1 day'
            elif delta.days > 2:
                grain = 'hour'
                db_interval = '1 hour'
            else:
                grain = 'minute'
                db_interval = '1 minute'
            
            limit = 1000
        except ValueError:
            return jsonify({'error': 'invalid date format'}), 400
    else:
        # 使用预设时间范围
        intervals = {
            '30m':   (now - timedelta(minutes=30),  '5 seconds', 360),
            '1h':    (now - timedelta(hours=1),     '10 seconds', 360),
            '6h':    (now - timedelta(hours=6),     '1 minute',  360),
            '12h':   (now - timedelta(hours=12),    '1 minute',  720),
            'hour':  (now - timedelta(hours=24),    '1 minute',  1440),
            'day':   (now - timedelta(days=7),      '10 minutes', 1008),
            'week':  (now - timedelta(weeks=8),     '1 week',    8),
            'month': (now - timedelta(days=365),    '1 month',   12),
            'year':  (now - timedelta(days=1825),   '1 year',    5)
        }
        
        # 校验时间粒度参数
        if unit not in intervals:
            return jsonify({'error': 'invalid unit'}), 400
            
        start_date, db_interval, limit = intervals[unit]
        grain = db_interval
        end_date = now

    try:
        # 连接数据库cursor(游标)
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 根据粒度选择时间桶表达式
        # month/year 使用 date_trunc，其他使用 time_bucket
        if db_interval == '1 month':
            bucket_expr = "date_trunc('month', time)"
        elif db_interval == '1 year':
            bucket_expr = "date_trunc('year', time)"
        else:
            bucket_expr = f"time_bucket(CAST('{db_interval}' AS INTERVAL), time)"

        # 构建 AVG 查询表达式
        avg_selects = ", ".join([f"AVG({f}) AS avg_{f}" for f in fields])
        
        # 执行时间桶聚合查询
        sql = f"""
            SELECT
                {bucket_expr} AS bucket,
                {avg_selects}
            FROM sensor_data
            WHERE time >= %s AND time <= %s
            GROUP BY bucket
            ORDER BY bucket ASC
        """
        cur.execute(sql, (start_date, end_date))
        rows = cur.fetchall()
        
        # 关闭数据库连接
        cur.close()
        conn.close()

        # 将时间戳对齐到时间桶边界的辅助函数
        def align_timestamp(dt, interval_str):
            if interval_str == '5 seconds':
                return dt.replace(second=(dt.second // 5) * 5, microsecond=0)
            elif interval_str == '10 seconds':
                return dt.replace(second=(dt.second // 10) * 10, microsecond=0)
            elif interval_str == '1 minute':
                return dt.replace(second=0, microsecond=0)
            elif interval_str == '10 minutes':
                return dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)
            elif interval_str == '1 hour':
                return dt.replace(minute=0, second=0, microsecond=0)
            elif interval_str == '1 day':
                return dt.replace(hour=0, minute=0, second=0, microsecond=0)
            elif interval_str == '1 week':
                # 对齐到周一
                monday = dt - timedelta(days=dt.weekday())
                return monday.replace(hour=0, minute=0, second=0, microsecond=0)
            return dt

        # 获取时间步长
        if db_interval == '5 seconds':
            step = timedelta(seconds=5)
        elif db_interval == '10 seconds':
            step = timedelta(seconds=10)
        elif db_interval == '1 minute':
            step = timedelta(minutes=1)
        elif db_interval == '10 minutes':
            step = timedelta(minutes=10)
        elif db_interval == '1 hour':
            step = timedelta(hours=1)
        elif db_interval == '1 day':
            step = timedelta(days=1)
        elif db_interval == '1 week':
            step = timedelta(weeks=1)
        else:
            step = None

        # 将时间戳转换为无时区的辅助函数
        def make_naive(dt):
            return dt.replace(tzinfo=None) if dt else None

        # 构建数据库结果的快速查找字典（O(1) 查询）
        data_map = {}
        for row in rows:
            if row[0]:
                data_map[make_naive(row[0])] = row[1:]

        # 对齐起始和结束时间到时间桶边界
        aligned_start = align_timestamp(start_date, db_interval)
        aligned_end = align_timestamp(end_date, db_interval)

        # 构建填充后的数据数组（处理缺失数据点）
        padded_rows = []
        if step is not None:
            current_time = aligned_start
            while current_time <= aligned_end:
                val = data_map.get(current_time)
                if val is not None:
                    # 有数据，直接使用
                    padded_rows.append((current_time, *val))
                else:
                    # 无数据，用 0.0 填充
                    padded_rows.append((current_time, *[0.0 for _ in fields]))
                current_time += step
        else:
            # month/year 粒度的回退处理（缺失数据极少）
            padded_rows = [(make_naive(r[0]), *r[1:]) for r in rows if r[0]]

        # 构造返回数据
        labels = []
        full_labels = [b[0].strftime('%Y-%m-%d %H:%M') for b in padded_rows]
        datasets = {f: [] for f in fields}
        
        for row in padded_rows:
            bucket = row[0]
            labels.append(bucket.strftime('%Y-%m-%d %H:%M'))
                
            # 填充各字段数据
            for idx, f in enumerate(fields):
                val = row[idx + 1]
                datasets[f].append(round(float(val), 2) if val is not None else 0.0)

        # 非自定义查询时，限制返回数据量（防止前端渲染压力）
        if not start_str: 
            labels = labels[-limit:]
            full_labels = full_labels[-limit:]
            for f in fields:
                datasets[f] = datasets[f][-limit:]

        return jsonify({'labels': labels, 'full_labels': full_labels, 'datasets': datasets})

    except Exception as e:
        # 错误处理
        log_error(f"Error in /trend: {e}")
        log_error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

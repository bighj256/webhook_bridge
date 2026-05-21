from flask import Flask, request, jsonify, render_template
import psycopg2
import psycopg2.extras
import logging
import json
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------- 日志配置 ----------
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(console_handler)

file_handler = RotatingFileHandler('/home/dean3002/webhook.log', maxBytes=10485760, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# 定义一个辅助方法，方便统一添加前缀
def log_info(msg):
    app.logger.info(f"[info] {msg}")

def log_warning(msg):
    app.logger.warning(f"[warning] {msg}")

def log_error(msg):
    app.logger.error(f"[error] {msg}")

# ---------- 数据库配置 ----------
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "sensor_data",
    "user": "postgres",
    "password": "QWEasdZXC123!"
}

# ---------- 健康检查 ----------
@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

# ---------- 原始数据接收（增强日志）----------
@app.route('/api/sensor_data', methods=['POST'])
def handle_sensor_data():
    try:
        data = request.get_json()
        if not data:
            log_warning("Received request without JSON data")
            return jsonify({"code": 400, "message": "No JSON data"}), 400

        # 记录收到的原始数据（可限制长度避免日志过大）
        raw_data_str = json.dumps(data, ensure_ascii=False)[:500]
        log_info(f"Received raw data: {raw_data_str}")

        # 处理 EMQX 嵌套 payload
        payload = data
        if 'payload' in data:
            payload_str = data['payload']
            if isinstance(payload_str, str):
                try:
                    payload = json.loads(payload_str)
                    log_info(f"Decoded payload from string: {json.dumps(payload, ensure_ascii=False)[:500]}")
                except json.JSONDecodeError as e:
                    log_error(f"Failed to decode payload JSON: {e}, raw payload string: {payload_str[:200]}")
                    return jsonify({"code": 400, "message": "Invalid payload JSON"}), 400
            else:
                payload = payload_str

        # 提取字段并校验
        temp = payload.get('temp')
        air_humi = payload.get('air_humi')
        soil_humi = payload.get('soil_humi')
        light = payload.get('light')
        ph = payload.get('ph')
        co2 = payload.get('co2')
        timestamp_unix = payload.get('time')

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

        if timestamp_unix is None:
            log_warning("Missing 'time' field in payload, cannot insert")
            return jsonify({"code": 400, "message": "Missing 'time' field"}), 400

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        insert_sql = """
            INSERT INTO sensor_data (time, temp, air_humi, soil_humi, light, ph, co2)
            VALUES (to_timestamp(%s), %s, %s, %s, %s, %s, %s)
        """
        params = (timestamp_unix, temp, air_humi, soil_humi, light, ph, co2)
        cur.execute(insert_sql, params)
        conn.commit()
        cur.close()
        conn.close()

        log_info(f"Data inserted successfully: temp={temp}, air_humi={air_humi}, time={timestamp_unix}")
        return jsonify({"code": 0, "message": "success"}), 200

    except psycopg2.Error as e:
        # 数据库错误（约束违反、类型错误等）
        log_error(f"Database error while inserting: {e}")
        # 尽可能输出导致错误的参数值（注意不要泄露敏感信息）
        if 'params' in locals():
            log_error(f"SQL parameters that caused error: {params}")
        else:
            log_error("Could not capture SQL parameters due to earlier exception.")
        log_error(traceback.format_exc())
        return jsonify({"code": 500, "message": f"Database error: {str(e)}"}), 500

    except Exception as e:
        log_error(f"Unexpected error: {e}")
        log_error(traceback.format_exc())
        return jsonify({"code": 500, "message": str(e)}), 500

# ---------- 最新数据（卡片用）----------
@app.route('/api/latest')
def latest_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
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
            log_warning("No data found in sensor_data table")
            return jsonify({"error": "no data"}), 404

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
        log_error(f"Error in /api/latest: {e}")
        log_error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ---------- 历史趋势 API ----------
@app.route('/api/trend/<param>')
def trend_data(param):
    """支持 param: ph, co2, soil_humi, light, temp, air_humi
       unit: hour, day, week, month, year
    """
    unit = request.args.get('unit', 'hour')
    allowed_fields = {
        'ph': 'ph',
        'co2': 'co2',
        'soil_humi': 'soil_humi',
        'light': 'light',
        'temp': 'temp',
        'air_humi': 'air_humi'
    }
    if param not in allowed_fields:
        log_warning(f"Invalid trend parameter: {param}")
        return jsonify({'error': 'invalid param'}), 400

    field = allowed_fields[param]

    now = datetime.now()
    intervals = {
        'hour':  (now - timedelta(hours=24),   'hour',     24),
        'day':   (now - timedelta(days=7),     'day',      7),
        'week':  (now - timedelta(weeks=8),    'week',     8),
        'month': (now - timedelta(days=365),   'month',    12),
        'year':  (now - timedelta(days=1825),  'year',     5)
    }
    if unit not in intervals:
        log_warning(f"Invalid time unit for trend: {unit}")
        return jsonify({'error': 'invalid unit'}), 400

    start_date, grain, limit = intervals[unit]

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        sql = f"""
            SELECT
                DATE_TRUNC('{grain}', time) AS bucket,
                AVG({field}) AS avg_value
            FROM sensor_data
            WHERE time >= %s
            GROUP BY bucket
            ORDER BY bucket ASC
        """
        cur.execute(sql, (start_date,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        labels = []
        values = []
        for bucket, avg_val in rows:
            if avg_val is None:
                continue
            if unit == 'hour':
                labels.append(bucket.strftime('%m-%d %H:00'))
            elif unit == 'day':
                labels.append(bucket.strftime('%m-%d (%a)'))
            elif unit == 'week':
                labels.append(f"W{bucket.isocalendar()[1]}")
            elif unit == 'month':
                labels.append(bucket.strftime('%Y-%m'))
            else:  # year
                labels.append(bucket.strftime('%Y'))
            values.append(round(float(avg_val), 2))

        labels = labels[-limit:]
        values = values[-limit:]

        log_info(f"Trend data for {param} with unit={unit}: returned {len(labels)} points")
        return jsonify({'labels': labels, 'values': values})

    except Exception as e:
        log_error(f"Error in /api/trend: {e}")
        log_error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ---------- 前端页面 ----------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

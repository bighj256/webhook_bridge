from flask import Flask, request, jsonify, render_template, Response
import psycopg2
import psycopg2.extras
import logging
import json
import traceback
import queue
import csv
import io
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------- SSE 客户端队列 ----------
sse_clients = []

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

        # 推送新数据到所有在线的 SSE 客户端
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
        for client_q in list(sse_clients):
            try:
                client_q.put_nowait(push_str)
            except queue.Full:
                pass

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

# ---------- SSE 推送接口 ----------
@app.route('/api/stream')
def stream():
    def event_stream():
        q = queue.Queue(maxsize=10)
        sse_clients.append(q)
        try:
            while True:
                # 阻塞等待，直到有新数据
                data = q.get()
                yield f"data: {data}\n\n"
        except GeneratorExit:
            if q in sse_clients:
                sse_clients.remove(q)

    # 声明该请求是一个长连接事件流
    return Response(event_stream(), mimetype="text/event-stream")

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

# ---------- 聚合统计 API ----------
@app.route('/api/stats')
def get_stats():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
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
        cur.close()
        conn.close()
        
        if not row or row[0] is None:
            return jsonify({})
            
        stats = {
            'temp': {'avg': round(row[0], 1), 'max': round(row[1], 1), 'min': round(row[2], 1)},
            'air_humi': {'avg': round(row[3], 1), 'max': round(row[4], 1), 'min': round(row[5], 1)},
            'soil_humi': {'avg': round(row[6], 1), 'max': round(row[7], 1), 'min': round(row[8], 1)},
            'light': {'avg': round(row[9], 1), 'max': round(row[10], 1), 'min': round(row[11], 1)},
            'ph': {'avg': round(row[12], 1), 'max': round(row[13], 1), 'min': round(row[14], 1)},
            'co2': {'avg': round(row[15], 1), 'max': round(row[16], 1), 'min': round(row[17], 1)}
        }
        return jsonify(stats)
    except Exception as e:
        log_error(f"Error in /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

# ---------- 数据导出 API ----------
@app.route('/api/export')
def export_data():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    params_str = request.args.get('params', 'temp')
    
    allowed_fields = ['ph', 'co2', 'soil_humi', 'light', 'temp', 'air_humi']
    fields = [f.strip() for f in params_str.split(',') if f.strip() in allowed_fields]
    if not fields:
        return jsonify({'error': 'invalid params'}), 400
        
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = f"SELECT time, {', '.join(fields)} FROM sensor_data "
        sql_params = []
        conditions = []
        
        if start_str:
            conditions.append("time >= %s")
            sql_params.append(start_str)
        if end_str:
            conditions.append("time <= %s")
            sql_params.append(end_str)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY time DESC LIMIT 10000"
        
        cur.execute(query, tuple(sql_params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Time'] + fields)
        for row in rows:
            writer.writerow([row[0].strftime('%Y-%m-%d %H:%M:%S')] + list(row[1:]))
            
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=sensor_data.csv"}
        )
    except Exception as e:
        log_error(f"Error in /api/export: {e}")
        return jsonify({'error': str(e)}), 500

# ---------- 历史趋势 API ----------
@app.route('/api/trend')
def trend_data():
    params_str = request.args.get('params', 'temp')
    unit = request.args.get('unit', 'hour')
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    allowed_fields = ['ph', 'co2', 'soil_humi', 'light', 'temp', 'air_humi']
    fields = [f.strip() for f in params_str.split(',') if f.strip() in allowed_fields][:2]
    
    if not fields:
        return jsonify({'error': 'invalid params'}), 400

    now = datetime.now()
    if start_str:
        try:
            def parse_dt(s):
                # 将 2026-02-22T02:18 格式化为 2026-02-22 02:18:00
                s = s.replace('Z', '').split('+')[0].replace('T', ' ').split('.')[0]
                if len(s) == 16:
                    s += ':00'
                return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

            start_date = parse_dt(start_str)
            end_date = parse_dt(end_str) if end_str else now
            
            delta = end_date - start_date
            if delta.days > 60:
                grain = 'day'
            elif delta.days > 2:
                grain = 'hour'
            else:
                grain = 'minute'
            
            limit = 1000
        except ValueError:
            return jsonify({'error': 'invalid date format'}), 400
    else:
        intervals = {
            'hour':  (now - timedelta(hours=24),   'hour',     24),
            'day':   (now - timedelta(days=7),     'day',      7),
            'week':  (now - timedelta(weeks=8),    'week',     8),
            'month': (now - timedelta(days=365),   'month',    12),
            'year':  (now - timedelta(days=1825),  'year',     5)
        }
        if unit not in intervals:
            return jsonify({'error': 'invalid unit'}), 400
        start_date, grain, limit = intervals[unit]
        end_date = now

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        avg_selects = ", ".join([f"AVG({f}) AS avg_{f}" for f in fields])
        
        sql = f"""
            SELECT
                DATE_TRUNC('{grain}', time) AS bucket,
                {avg_selects}
            FROM sensor_data
            WHERE time >= %s AND time <= %s
            GROUP BY bucket
            ORDER BY bucket ASC
        """
        cur.execute(sql, (start_date, end_date))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        labels = []
        datasets = {f: [] for f in fields}
        
        for row in rows:
            bucket = row[0]
            if unit == 'hour' or grain == 'hour':
                labels.append(bucket.strftime('%m-%d %H:00'))
            elif unit == 'day' or grain == 'day':
                labels.append(bucket.strftime('%m-%d'))
            elif unit == 'week':
                labels.append(f"W{bucket.isocalendar()[1]}")
            elif unit == 'month':
                labels.append(bucket.strftime('%Y-%m'))
            elif grain == 'minute':
                labels.append(bucket.strftime('%H:%M'))
            else:  
                labels.append(bucket.strftime('%Y'))
                
            for idx, f in enumerate(fields):
                val = row[idx + 1]
                datasets[f].append(round(float(val), 2) if val is not None else None)

        if not start_str: 
            labels = labels[-limit:]
            for f in fields:
                datasets[f] = datasets[f][-limit:]

        return jsonify({'labels': labels, 'datasets': datasets})

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

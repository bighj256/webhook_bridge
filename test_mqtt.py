#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import json
import random
import subprocess

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "farm/sensor/collect"

def generate_mock_data():
    """生成带有当前时间戳的随机模拟数据"""
    return {
        "temp": round(random.uniform(18.0, 42.0), 1),
        "air_humi": round(random.uniform(40.0, 75.0), 1),
        "soil_humi": round(random.uniform(30.0, 70.0), 1),
        "light": int(random.uniform(2000, 12000)),
        "ph": round(random.uniform(6.0, 7.5), 1),
        "co2": int(random.uniform(400, 900)),
        "time": int(time.time()) # 获取当前最新的 Unix 时间戳
    }

def main():
    print(f"[*] 开始向 {MQTT_HOST}:{MQTT_PORT} 发送模拟数据...")
    print(f"[*] 目标主题: {MQTT_TOPIC}")
    print("[*] 按 Ctrl+C 停止测试\n")
    
    try:
        while True:
            data = generate_mock_data()
            payload = json.dumps(data)
            
            # 使用列表传参更加安全，跨平台兼容性更好，不需要担心 shell 下的引号转义问题
            cmd = [
                "mosquitto_pub",
                "-h", str(MQTT_HOST),
                "-p", str(MQTT_PORT),
                "-t", MQTT_TOPIC,
                "-m", payload
            ]
            
            print(f"发送: {payload}")
            
            # 执行命令 (兼容 Python 3.6)
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            
            if result.returncode != 0:
                print(f"[!] 发送失败: {result.stderr}")
            
            # 每隔 5 秒发一条
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n[*] 测试结束")
    except FileNotFoundError:
        print("\n[!] 找不到 mosquitto_pub 命令。")
        print("请确保已安装 MQTT 客户端：")
        print(" - CentOS: sudo yum install mosquitto-clients")
        print(" - Ubuntu: sudo apt install mosquitto-clients")

if __name__ == "__main__":
    main()

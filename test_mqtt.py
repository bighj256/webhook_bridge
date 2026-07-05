#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import json
import random
import paho.mqtt.client as mqtt

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "farm/sensor/collect"

def generate_mock_data():
    return {
        "temp": round(random.uniform(18.0, 42.0), 1),
        "air_humi": round(random.uniform(40.0, 75.0), 1),
        "soil_humi": round(random.uniform(30.0, 70.0), 1),
        "light": int(random.uniform(2000, 12000)),
        "ph": round(random.uniform(6.0, 7.5), 1),
        "co2": int(random.uniform(400, 900)),
        "time": int(time.time())
    }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[*] MQTT连接成功")
    else:
        print(f"[!] MQTT连接失败，错误码: {rc}")

def main():
    print(f"[*] 开始向 {MQTT_HOST}:{MQTT_PORT} 发送模拟数据...")
    print(f"[*] 目标主题: {MQTT_TOPIC}")
    print("[*] 按 Ctrl+C 停止测试\n")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        
        while True:
            data = generate_mock_data()
            payload = json.dumps(data)
            
            result = client.publish(MQTT_TOPIC, payload, qos=0)
            result.wait_for_publish()
            
            if result.is_published():
                print(f"发送: {payload}")
            else:
                print(f"[!] 发送失败")
            
            time.sleep(5)
            
    except ConnectionRefusedError:
        print("\n[!] 无法连接到MQTT Broker，请确保已安装并启动MQTT服务")
        print("推荐安装方式：")
        print("  EMQX: https://www.emqx.io/zh/downloads")
    except KeyboardInterrupt:
        print("\n[*] 测试结束")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
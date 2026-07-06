#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import json
import random
from paho.mqtt import client as mqtt_client

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "farm/sensor/collect"
MQTT_USERNAME = "TestUser"
MQTT_PASSWORD = "TestPassword"


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


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[*] MQTT 连接成功")
    else:
        print(f"[!] MQTT 连接失败，错误码: {rc}")


def on_publish(client, userdata, mid, reason_code=None, properties=None):
    pass


def main():
    print(f"[*] 开始向 {MQTT_HOST}:{MQTT_PORT} 发送模拟数据...")
    print(f"[*] 目标主题: {MQTT_TOPIC}")
    print("[*] 按 Ctrl+C 停止测试\n")

    client_id = f"test_mqtt_{random.randint(0, 10000)}"
    client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311)
    client.on_connect = on_connect
    client.on_publish = on_publish

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            data = generate_mock_data()
            payload = json.dumps(data)

            result = client.publish(MQTT_TOPIC, payload, qos=0)
            status = result[0]

            if status == 0:
                print(f"发送: {payload}")
            else:
                print(f"[!] 发送失败，状态码: {status}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n[*] 测试结束")
    except Exception as e:
        print(f"\n[!] 发生错误: {e}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

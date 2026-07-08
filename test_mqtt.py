"""
MQTT 测试数据生成器

用于模拟传感器数据上报场景，生成符合温室环境参数范围的随机数据，
并通过 MQTT 协议发送到 EMQX Broker，验证 webhook_bridge 的数据接收功能。

测试场景:
    - EMQX Broker 未启动时测试连接失败情况
    - 数据接收功能验证
    - SSE 实时推送功能验证
    - 日志记录功能验证

使用方法:
    1. 确保 EMQX Broker 正在运行
    2. python test_mqtt.py
    3. 观察控制台输出和数据接收日志

注意:
    - 默认主题: farm/sensor/collect
    - 发送间隔: 5 秒/次
    - QoS: 0（最多一次，不保证送达）
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import json
import random
from paho.mqtt import client as mqtt_client

# ==============================================================================
# MQTT 连接配置
# ==============================================================================
MQTT_HOST = "127.0.0.1"           # MQTT Broker 地址（本地）
MQTT_PORT = 1883                  # MQTT Broker 端口
MQTT_TOPIC = "farm/sensor/collect"  # 发布主题（与 EMQX 配置一致）
MQTT_USERNAME = "TestUser"        # 用户名
MQTT_PASSWORD = "TestPassword"    # 密码

"""
    生成模拟传感器数据
    生成符合温室环境参数范围的随机数据，用于测试数据接收功能。
"""
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

"""
    MQTT 连接回调函数
    当 MQTT 客户端与 Broker 建立连接时触发此函数。
    参数 rc: 连接结果代码（0 表示成功）
"""
def on_connect(client, userdata, flags, rc, properties=None):
    
    if rc == 0:
        print("[*] MQTT 连接成功")
    else:
        print(f"[!] MQTT 连接失败，错误码: {rc}")

"""
    MQTT 发布回调函数
"""
def on_publish(client, userdata, mid, reason_code=None, properties=None):
    pass  # 发布成功与否不影响测试流程

"""
        主测试函数
测试流程:
        1. 创建 MQTT 客户端（使用随机 client_id）
        2. 设置连接和发布回调函数
        3. 连接到 MQTT Broker
        4. 进入发送循环（每隔 5 秒发送一次数据）
        5. 捕获中断信号和异常，优雅退出
"""
def main():
    print(f"[*] 开始向 {MQTT_HOST}:{MQTT_PORT} 发送模拟数据...")
    print(f"[*] 目标主题: {MQTT_TOPIC}")
    print("[*] 按 Ctrl+C 停止测试\n")

    # 创建 MQTT 客户端（使用随机 client_id）
    client_id = f"test_mqtt_{random.randint(0, 10000)}"
    client = mqtt_client.Client(client_id=client_id, protocol=mqtt_client.MQTTv311)
    client.on_connect = on_connect
    client.on_publish = on_publish

    # 如果配置了用户名密码，进行认证
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    # 连接到 MQTT Broker（keepalive=60 秒无数据则断开重连）
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)

    # 启动 MQTT 循环（非阻塞，自动处理心跳和重连）
    client.loop_start()

    try:
        # 无限循环发送数据
        while True:
            # 生成模拟数据
            data = generate_mock_data()
            # 转换为 JSON 字符串
            payload = json.dumps(data)

            # 发布消息到指定主题
            result = client.publish(MQTT_TOPIC, payload, qos=0)
            # 获取发布状态（result[0] 是状态码，0 表示成功）
            status = result[0]

            # 输出发送状态
            if status == 0:
                print(f"发送: {payload}")
            else:
                print(f"[!] 发送失败，状态码: {status}")

            # 等待 5 秒后发送下一条数据
            time.sleep(5)

    except KeyboardInterrupt:
        # 用户按 Ctrl+C 中断测试
        print("\n[*] 测试结束")
    except Exception as e:
        # 捕获其他异常
        print(f"\n[!] 发生错误: {e}")
    finally:
        # 停止 MQTT 循环（清理资源）
        client.loop_stop()
        # 断开连接
        client.disconnect()


if __name__ == "__main__":
    main()

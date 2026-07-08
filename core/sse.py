"""
SSE 客户端管理模块

负责管理 Server-Sent Events (SSE) 的客户端连接，实现实时数据推送功能。

核心特性:
    - 客户端队列管理：每个客户端连接对应一个消息队列
    - 广播机制：支持向所有在线客户端推送实时数据
    - 非阻塞写入：队列满时自动丢弃，避免阻塞主线程
    - 线程安全：遍历前复制列表，防止并发修改问题

SSE (Server-Sent Events) 是一种服务器向客户端推送数据的技术，
相比 WebSocket,SSE 更轻量，适合单向数据推送场景。

工作原理:
    1. 客户端通过 EventSource 连接 /api/stream 接口
    2. 服务端为每个客户端创建一个消息队列
    3. 当有新数据时，通过 broadcast_sse() 广播到所有队列
    4. 客户端队列中的数据通过 SSE 流推送至前端
    5. 客户端断开连接时，队列从列表中移除
"""
import queue

# SSE 客户端队列列表，每个队列对应一个客户端连接
# 当有新数据时，遍历此列表将数据放入每个客户端的队列中
sse_clients = []


#注册新的 SSE 客户端队列
"""
    当客户端通过 EventSource 连接 /api/stream 接口时，
    会创建一个消息队列并通过此函数注册到全局列表中。
"""
def add_sse_client(q):
    sse_clients.append(q)

#移除 SSE 客户端队列
"""
    当客户端断开连接时（如关闭页面、网络断开），
    通过此函数将客户端队列从全局列表中移除，避免向已断开的连接推送数据。
"""
def remove_sse_client(q):
    
    if q in sse_clients:
        sse_clients.remove(q)


#广播数据到所有 SSE 客户端
"""
    将传感器数据广播到所有在线的 SSE 客户端，实现实时数据推送。
    使用非阻塞方式写入队列，队列满时自动丢弃，确保不会阻塞主线程。
    注意:
        - 使用 list() 复制列表，防止遍历过程中列表被并发修改
        - 使用 put_nowait() 非阻塞写入，避免队列满时阻塞
        - 队列满时（queue.Full）静默丢弃数据，不记录错误
"""
def broadcast_sse(data_str):
    for client_q in list(sse_clients):
        try:
            # 非阻塞写入，队列满时丢弃（避免阻塞主线程）
            client_q.put_nowait(data_str)
        except queue.Full:
            # 队列已满，跳过此客户端（数据可能已过期）
            pass
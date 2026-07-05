#SSE客户端管理模块
import queue

# SSE 客户端队列列表，每个队列对应一个客户端连接
sse_clients = []

def add_sse_client(q):
    """注册新的 SSE 客户端队列"""
    sse_clients.append(q)

def remove_sse_client(q):
    """移除 SSE 客户端队列（客户端断开时调用）"""
    if q in sse_clients:
        sse_clients.remove(q)

def broadcast_sse(data_str):
    """广播数据到所有 SSE 客户端
    参数:
        data_str: 要广播的 JSON 字符串数据
    """
    # 使用 list() 复制防止遍历过程中列表被修改
    for client_q in list(sse_clients):
        try:
            # 非阻塞写入，队列满时丢弃（避免阻塞）
            client_q.put_nowait(data_str)
        except queue.Full:
            pass

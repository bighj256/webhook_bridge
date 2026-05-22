import queue

# SSE 客户端队列
sse_clients = []

def add_sse_client(q):
    sse_clients.append(q)

def remove_sse_client(q):
    if q in sse_clients:
        sse_clients.remove(q)

def broadcast_sse(data_str):
    for client_q in list(sse_clients):
        try:
            client_q.put_nowait(data_str)
        except queue.Full:
            pass

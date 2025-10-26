# server.py
import socket
import threading
import json
import uuid
from queue import Queue

from queue_bus import task_queue          # cola que simula RabbitMQ
from worker import Worker                 # workers (threads) que procesan tareas
from storage import init_sqlite           # crea/asegura la DB

HOST = "127.0.0.1"
PORT = 5001
NUM_WORKERS = 4
BACKLOG = 50

def recv_line(sock) -> str:
    """Lee una línea (JSONL) terminada en '\n' desde el socket."""
    buf = bytearray()
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        buf.extend(chunk)
        if b"\n" in chunk:
            break
    if not buf:
        return ""
    return buf.split(b"\n", 1)[0].decode("utf-8")

def handle_client(conn: socket.socket, addr):
    """Atiende a un cliente: recibe JSONL, encola tarea y responde resultado."""
    try:
        while True:
            line = recv_line(conn)
            if not line:
                break
            try:
                req = json.loads(line)
            except Exception:
                resp = {"status": "error", "message": "JSON inválido"}
                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                continue

            # Cola de respuesta para sincronizar con el worker que procese esta tarea
            reply_q = Queue(maxsize=1)
            task = {
                "id": str(uuid.uuid4()),
                "op": req.get("op", "echo"),
                "data": req.get("data", ""),
                "reply_queue": reply_q,
            }

            # Encolamos la tarea para que la tome algún worker del pool
            task_queue.put(task)

            # Esperamos el resultado del worker y respondemos al cliente
            result = reply_q.get()
            conn.sendall((json.dumps(result) + "\n").encode("utf-8"))
    except Exception as e:
        try:
            conn.sendall((json.dumps({"status": "error", "message": str(e)}) + "\n").encode("utf-8"))
        except Exception:
            pass
    finally:
        conn.close()

def start_server():
    # Inicializa almacenamiento (tabla results en SQLite)
    init_sqlite()

    # Lanza pool de workers en modo daemon
    for i in range(NUM_WORKERS):
        Worker(task_queue, name=f"worker-{i+1}").start()

    # Servidor TCP concurrente
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(BACKLOG)
        print(f"Servidor en {HOST}:{PORT} con {NUM_WORKERS} workers. Esperando clientes...")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()

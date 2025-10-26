# server.py
import socket
import threading
import json
import uuid
import logging
from queue import Queue, Empty

from queue_bus import task_queue          # cola que simula RabbitMQ
from worker import Worker                 # workers (threads) que procesan tareas
from storage import init_sqlite           # crea/asegura la DB

HOST = "127.0.0.1"
PORT = 5001
NUM_WORKERS = 4
BACKLOG = 64
WORKER_REPLY_TIMEOUT = 10.0  # segundos

ALLOWED_OPS = {"uppercase", "hash", "echo"}

# --- Logging base ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s"
)

def recv_line(sock: socket.socket) -> str:
    """Lee una línea (JSONL) terminada en '\\n' desde el socket."""
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
    return buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")

def handle_client(conn: socket.socket, addr: tuple[str, int]) -> None:
    """Atiende a un cliente: recibe JSONL, encola tarea y responde resultado."""
    logging.info(f"cliente conectado: {addr}")
    try:
        while True:
            line = recv_line(conn)
            if not line:
                break

            # Parseo JSON
            try:
                req = json.loads(line)
            except Exception:
                resp = {"status": "error", "message": "JSON inválido"}
                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                continue

            op = req.get("op", "echo")
            data = req.get("data", "")

            if op not in ALLOWED_OPS:
                resp = {"status": "error", "message": f"op no soportada: {op}"}
                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                continue

            # Cola de respuesta (RPC simple)
            reply_q: Queue = Queue(maxsize=1)
            task = {
                "id": str(uuid.uuid4()),
                "op": op,
                "data": data,
                "reply_queue": reply_q,
            }

            # Encolamos y esperamos el resultado
            logging.info(f"tarea recibida: id={task['id']} op={op}")
            task_queue.put(task)

            try:
                result = reply_q.get(timeout=WORKER_REPLY_TIMEOUT)
            except Empty:
                logging.error(f"timeout esperando worker, id={task['id']}")
                result = {"status": "error", "message": "timeout esperando al worker"}

            # Respondemos al cliente
            conn.sendall((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))

    except Exception as e:
        logging.exception("error atendiendo cliente")
        try:
            conn.sendall((json.dumps({"status": "error", "message": str(e)}) + "\n").encode("utf-8"))
        except Exception:
            pass
    finally:
        logging.info(f"cliente desconectado: {addr}")
        try:
            conn.close()
        except Exception:
            pass

def start_server() -> None:
    # Inicializa almacenamiento (tabla results en SQLite)
    init_sqlite()

    # Lanza pool de workers en modo daemon
    for i in range(NUM_WORKERS):
        Worker(task_queue, name=f"worker-{i+1}").start()

    # Servidor TCP concurrente
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # evitar "Address already in use"
        s.bind((HOST, PORT))
        s.listen(BACKLOG)
        logging.info(f"Servidor en {HOST}:{PORT} con {NUM_WORKERS} workers. Esperando clientes...")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()

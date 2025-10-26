# worker.py (versión corregida)
import threading, time, hashlib
from storage import save_result_sqlite, save_result_s3like

class Worker(threading.Thread):
    def __init__(self, task_queue, name):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.name = name

    def run(self):
        while True:
            task = self.task_queue.get()  # dict: {id, op, data, reply_queue}
            try:
                result = self.process(task)

                # ⚠️ IMPORTANTE: crear una versión "segura" de la tarea sin reply_queue
                safe_task = {k: v for k, v in task.items() if k != "reply_queue"}

                # Persistimos usando la tarea "segura" (sin objetos no serializables)
                save_result_sqlite(safe_task, result)
                save_result_s3like(task["id"], {"task": safe_task, "result": result})

                # Devolvemos el resultado al servidor
                task["reply_queue"].put(result)

            except Exception as e:
                task["reply_queue"].put({"status": "error", "message": str(e)})
            finally:
                self.task_queue.task_done()

    def process(self, task: dict) -> dict:
        """
        Operaciones de ejemplo:
        - op="uppercase": convierte a MAYÚSCULAS
        - op="hash": SHA256
        - op desconocida: echo
        """
        op = task.get("op")
        data = str(task.get("data", ""))

        time.sleep(0.2)  # simula trabajo
        if op == "uppercase":
            return {"status": "ok", "worker": self.name, "result": data.upper()}
        elif op == "hash":
            h = hashlib.sha256(data.encode("utf-8")).hexdigest()
            return {"status": "ok", "worker": self.name, "result": h}
        else:
            return {"status": "ok", "worker": self.name, "result": f"echo:{data}"}

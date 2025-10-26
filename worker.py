# worker.py (logging, manejo de errores por operación, artefacto JSON)
import threading
import time
import hashlib
import logging
import random
from storage import save_result_sqlite, save_result_s3like

# (el basicConfig lo arma server.py; si corrés este módulo solo, descomentá:)
# logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s")

class Worker(threading.Thread):
    def __init__(self, task_queue, name: str):
        super().__init__(daemon=True, name=name)
        self.task_queue = task_queue

    def run(self) -> None:
        while True:
            task = self.task_queue.get()  # dict: {id, op, data, reply_queue}
            try:
                result = self.process(task)

                # ⚠️ IMPORTANTE: crear una versión "segura" de la tarea sin reply_queue
                safe_task = {k: v for k, v in task.items() if k != "reply_queue"}

                # Persistimos resultado (DB + "S3" JSON)
                path = save_result_s3like(task["id"], {"task": safe_task, "result": result})
                result_with_artifact = {**result, "artifact_path": path}
                save_result_sqlite(safe_task, result_with_artifact)

                # Devolvemos el resultado al servidor
                task["reply_queue"].put(result_with_artifact)

            except Exception as e:
                logging.exception("error en worker")
                task["reply_queue"].put({"status": "error", "worker": self.name, "message": str(e)})
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

        # simular trabajo variable
        time.sleep(random.uniform(0.1, 0.4))

        try:
            if op == "uppercase":
                out = data.upper()
            elif op == "hash":
                out = hashlib.sha256(data.encode("utf-8")).hexdigest()
            else:
                out = f"echo:{data}"

            logging.info(f"{self.name} procesó id={task.get('id')} op={op}")
            return {"status": "ok", "worker": self.name, "result": out}

        except Exception as e:
            logging.exception(f"{self.name} falló procesando op={op}")
            return {"status": "error", "worker": self.name, "message": str(e)}

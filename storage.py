import os
import json
import time
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "results.sqlite"

def init_sqlite() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                result TEXT,
                ts TEXT
            )"""
        )
        conn.commit()

def save_result_sqlite(task: dict, result: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO results(task, result, ts) VALUES (?, ?, ?)",
            (
                json.dumps(task, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                time.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()

# “S3” simulado: guardamos archivos JSON en /data
def save_result_s3like(task_id: str, payload: dict) -> str:
    out = DATA_DIR / f"result_{task_id}.json"
    # Intento robusto de escritura
    tmp = str(out) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, out)  # atómico en la mayoría de SOs
    return str(out)

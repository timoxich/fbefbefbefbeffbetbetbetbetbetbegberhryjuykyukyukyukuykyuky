import sqlite3
import random
import string
import subprocess
from threading import Thread
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

app = FastAPI()
DB_PATH = "db.sqlite"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            is_active INTEGER DEFAULT 1,
            hwid TEXT DEFAULT ''
        )
        """)
        conn.commit()

init_db()

def get_conn():
    return sqlite3.connect(DB_PATH)

def get_key_data(key: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT is_active, hwid FROM keys WHERE key = ?", (key,))
        return cur.fetchone()

def update_hwid(key: str, hwid: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE keys SET hwid = ? WHERE key = ?", (hwid, key))
        conn.commit()

def reset_key_hwid(key: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE keys SET hwid = '' WHERE key = ?", (key,))
        conn.commit()

def insert_key(key: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO keys (key, is_active, hwid) VALUES (?, 1, '')", (key,))
        conn.commit()

def generate_key():
    return "ELEVENX_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class KeyModel(BaseModel):
    key: str

@app.get("/TKVYLeXu_check")
def check(key: str = Query(...), hwid: str = Query(...)):
    result = get_key_data(key)
    if not result:
        return {"valid": False}
    is_active, stored_hwid = result
    if not is_active:
        return {"valid": False}
    if stored_hwid in ("", None, hwid):
        if not stored_hwid:
            update_hwid(key, hwid)
        return {"valid": True}
    return {"valid": False}

@app.post("/MmsTdaqL_reset_hwid")
def reset(data: KeyModel):
    if not get_key_data(data.key):
        return {"success": False}
    reset_key_hwid(data.key)
    return {"success": True}

@app.api_route("/generate_key", methods=["GET", "POST"])
def generate_key_endpoint():
    key = generate_key()
    insert_key(key)
    return {"success": True, "key": key}

@app.get("/ZJEfYIMk_activate_key")
def activate_key(code: str = Query(...), hwid: str = Query(...)):
    result = get_key_data(code)
    if not result:
        return {"success": False, "message": "Ключ не найден"}
    is_active, stored_hwid = result
    if not is_active:
        return {"success": False, "message": "Ключ не активен"}
    if stored_hwid not in ("", None, hwid):
        return {"success": False, "message": "Ключ привязан к другому устройству"}
    if stored_hwid in ("", None):
        update_hwid(code, hwid)
    return {"success": True, "key": code}

@app.get("/moASnrwD_get_key_info")
def info(key: str = Query(...)):
    result = get_key_data(key)
    if not result:
        return {"found": False}
    is_active, hwid = result
    return {
        "found": True,
        "key": key,
        "is_active": bool(is_active),
        "hwid": hwid or "не привязано",
        "dlc_status": "UNDETECTED"
    }

def run_bot():
    subprocess.run(["python3", "main.py"])

if __name__ == "__main__":
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()

    import uvicorn

    uvicorn.run("server_fastapi:app", host="0.0.0.0", port=8000)

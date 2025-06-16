import sqlite3
import random
import string
import subprocess
from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI()
DB_PATH = "db.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        is_active INTEGER DEFAULT 1,
        hwid TEXT DEFAULT ''
    )
    """)
    conn.commit()
    conn.close()

init_db()

def get_conn():
    return sqlite3.connect(DB_PATH)

def get_key_data(key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT is_active, hwid FROM keys WHERE key = ?", (key,))
    result = cur.fetchone()
    conn.close()
    return result

def update_hwid(key, hwid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE keys SET hwid = ? WHERE key = ?", (hwid, key))
    conn.commit()
    conn.close()

def reset_key_hwid(key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE keys SET hwid = '' WHERE key = ?", (key,))
    conn.commit()
    conn.close()

def insert_key(key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO keys (key, is_active, hwid) VALUES (?, 1, '')", (key,))
    conn.commit()
    conn.close()

def generate_key():
    return "NEREST_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class KeyModel(BaseModel):
    key: str

@app.get("/TKVYLeXu_check")
def check(key: str, hwid: str = Query(...)):
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
    else:
        return {"valid": False}

@app.post("/MmsTdaqL_reset_hwid")
def reset(data: KeyModel):
    if not get_key_data(data.key):
        return {"success": False}
    reset_key_hwid(data.key)
    return {"success": True}

@app.get("/ZJEfYIMk_activate_key")
def activate(code: str):
    key = generate_key()
    insert_key(key)
    return {"success": True, "key": key}

@app.get("/moASnrwD_get_key_info")
def info(key: str):
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

if __name__ == "__main__":
    subprocess.Popen(["python3", "main.py"])
    import uvicorn
    uvicorn.run("server_fastapi:app", host="0.0.0.0", port=8000)
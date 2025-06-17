import sqlite3
import random
import string
import subprocess
from threading import Thread
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "keys.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        user_id INTEGER
    )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def generate_key():
    return 'ELEVENX_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

@app.on_event("startup")
def on_startup():
    init_db()

class Key(BaseModel):
    key: str
    user_id: int

@app.post("/generate_key/")
def generate_key_endpoint():
    key = generate_key()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO keys (key) VALUES (?)', (key,))
    conn.commit()
    conn.close()
    return {"key": key}

@app.post("/activate_key/")
def activate_key(key: str = Query(...), user_id: int = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_active, user_id FROM keys WHERE key = ?', (key,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Key not found")
    is_active, current_user_id = result
    if not is_active:
        conn.close()
        raise HTTPException(status_code=400, detail="Key is not active")
    if current_user_id is not None and current_user_id != user_id:
        conn.close()
        raise HTTPException(status_code=400, detail="Key is already in use by another user")
    cursor.execute('UPDATE keys SET user_id = ? WHERE key = ?', (user_id, key))
    conn.commit()
    conn.close()
    return {"success": True, "key": key}

@app.get("/check_key/")
def check_key(user_id: int = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, is_active FROM keys WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Key not found")
    key, is_active = result
    if not is_active:
        return {"valid": False, "detail": "Key is not active"}
    return {"valid": True, "key": key}

@app.get("/get_key_info/")
def get_key_info(key: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, is_active, user_id FROM keys WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Key not found")
    key, is_active, user_id = result
    return {
        "key": key,
        "is_active": is_active,
        "user_id": user_id,
        "dlc_status": "UNDETECTED"
    }

def run_bot():
    subprocess.run(["python3", "main.py"])

if __name__ == "__main__":
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

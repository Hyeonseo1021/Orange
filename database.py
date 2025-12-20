# database.py
import sqlite3
from datetime import datetime

DB_FILE = "chat_history.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 대화방(세션) 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. 메시지 테이블 (session_id 추가)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)
    conn.commit()
    conn.close()

def create_session(title="새로운 대화"):
    """새 대화방 만들기"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (title) VALUES (?)", (title,))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_sessions():
    """대화방 목록 가져오기"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    return [dict(row) for row in cursor.fetchall()]

def save_message(session_id, role, content):
    """특정 대화방에 메시지 저장"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    
    # (선택) 첫 질문일 경우 대화방 제목을 질문 내용으로 업데이트
    if role == "user":
        cursor.execute("SELECT count(*) as cnt FROM messages WHERE session_id = ?", (session_id,))
        if cursor.fetchone()['cnt'] == 1:
            short_title = content[:15] + "..." if len(content) > 15 else content
            cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (short_title, session_id))
            
    conn.commit()
    conn.close()

def load_messages(session_id):
    """특정 대화방의 메시지 불러오기"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    return [dict(row) for row in cursor.fetchall()]
    
def update_session_title(session_id, new_title):
    """세션 제목 업데이트 (이 함수가 없어서 에러가 났습니다)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()
    
def delete_session(session_id):
    """대화방 삭제"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
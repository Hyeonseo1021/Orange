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
    
    # 1. 대화방(세션)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. 메시지
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

    # 3. 퀴즈 결과
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER,
        total INTEGER,
        topic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. 복습 노트
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        correct_answer TEXT,
        my_answer TEXT,
        explanation TEXT,
        is_reviewed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# --- 세션/메시지 ---
def create_session(title="새로운 대화"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (title) VALUES (?)", (title,))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid

def get_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
    return [dict(row) for row in cursor.fetchall()]

def save_message(session_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    if role == "user":
        cursor.execute("SELECT count(*) as cnt FROM messages WHERE session_id = ?", (session_id,))
        if cursor.fetchone()['cnt'] == 1:
            short_title = content[:15] + "..." if len(content) > 15 else content
            cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (short_title, session_id))
    conn.commit()
    conn.close()

def load_messages(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    return [dict(row) for row in cursor.fetchall()]

def update_session_title(session_id, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()
    
def delete_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

# --- 퀴즈/복습 ---
def save_quiz_result(score, total, topic="General"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_results (score, total, topic) VALUES (?, ?, ?)", (score, total, topic))
    conn.commit()
    conn.close()

def get_quiz_results():
    """[추가됨] 퀴즈 기록 가져오기"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quiz_results ORDER BY created_at DESC")
    return [dict(row) for row in cursor.fetchall()]

def add_review_note(question, correct_answer, my_answer, explanation):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO review_notes (question, correct_answer, my_answer, explanation) VALUES (?, ?, ?, ?)",
        (question, correct_answer, my_answer, explanation)
    )
    conn.commit()
    conn.close()

def get_review_notes(only_unreviewed=True):
    conn = get_connection()
    cursor = conn.cursor()
    if only_unreviewed:
        cursor.execute("SELECT * FROM review_notes WHERE is_reviewed = 0 ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM review_notes ORDER BY created_at DESC")
    return [dict(row) for row in cursor.fetchall()]

def mark_reviewed(note_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE review_notes SET is_reviewed = 1 WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
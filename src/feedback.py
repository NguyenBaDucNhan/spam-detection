"""Lưu phản hồi vào SQLite; chỉ lưu nội dung khi save_text=True."""
from datetime import datetime, timezone
import sqlite3
from uuid import uuid4
from .settings import load_config, project_path

def save_feedback(text, prediction, actual_label, *, save_text=False, db_path=None):
    """Trả về ID phản hồi vừa lưu. Lịch sử kiểm tra được quản lý ở history.py."""
    if actual_label not in ('ham', 'spam'):
        raise ValueError('Nhãn phản hồi không hợp lệ.')
    path = project_path(db_path or load_config()['feedback_path'])
    path.parent.mkdir(parents=True, exist_ok=True)
    feedback_id = str(uuid4())
    if save_text:
        saved_message = text
    else:
        saved_message = None

    # Dấu ? trong SQL giúp truyền dữ liệu riêng, không nối nội dung vào câu lệnh.
    with sqlite3.connect(path, timeout=15) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, model_id TEXT NOT NULL,
            predicted_label TEXT NOT NULL, actual_label TEXT NOT NULL,
            score REAL NOT NULL, message TEXT
        )""")
        values = (
            feedback_id,
            datetime.now(timezone.utc).isoformat(),
            prediction.model_id,
            prediction.label,
            actual_label,
            prediction.score,
            saved_message,
        )
        connection.execute('INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?, ?)', values)
    return feedback_id

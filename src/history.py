"""Lưu lịch sử chung trên máy. Chưa có phân tách theo tài khoản người dùng."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
import sqlite3
from uuid import uuid4

from .settings import load_config, project_path

STATUSES = {
    'message': {'spam', 'ham'},
    'link': {'danger', 'no_match', 'error'},
}


def database_path(db_path=None):
    """Ưu tiên: tham số hàm → biến môi trường → cấu hình → đường dẫn mặc định."""
    if db_path:
        return project_path(db_path)
    environment_path = os.environ.get('SPAM_HISTORY_DB')
    if environment_path:
        return project_path(environment_path)
    config = load_config()
    configured_path = config.get('history_path', 'data/history.sqlite3')
    return project_path(configured_path)


@contextmanager
def connect(db_path=None):
    """Mở database cho một khối `with`; tự commit/rollback và đóng kết nối."""
    path = database_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    try:
        with db:
            db.row_factory = sqlite3.Row
            db.create_function('casefold', 1, lambda value: str(value or '').casefold())
            db.execute('PRAGMA secure_delete = ON')
            db.execute('''CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('message', 'link')),
                content TEXT NOT NULL, status TEXT NOT NULL,
                score REAL, model_id TEXT, details TEXT NOT NULL
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS history_time ON history(created_at DESC)')
            yield db
    finally:
        db.close()


def _save(kind, content, status, *, score=None, model_id=None, details=None, db_path=None):
    """Hàm nội bộ dùng chung để ghi một lượt và trả về ID của lượt đó."""
    if kind not in STATUSES or status not in STATUSES[kind]:
        raise ValueError('Loại kiểm tra hoặc kết quả không hợp lệ.')
    if not isinstance(content, str) or not content.strip() or len(content) > 20000:
        raise ValueError('Nội dung lịch sử không hợp lệ.')
    record_id = str(uuid4())
    with connect(db_path) as db:
        values = (
            record_id,
            datetime.now(timezone.utc).isoformat(),
            kind,
            content,
            status,
            score,
            model_id,
            json.dumps(details or {}, ensure_ascii=False),
        )
        db.execute('INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?, ?)', values)
    return record_id


def save_message(text, prediction, *, db_path=None):
    """Lưu kết quả tin nhắn, dùng đúng định dạng Prediction của predictor.py."""
    return _save(
        'message', text, prediction.label,
        score=prediction.score,
        model_id=prediction.model_id,
        details={'indicators': prediction.indicators},
        db_path=db_path,
    )


def save_link(url, result, *, db_path=None):
    # Chỉ chép các trường cho phép, không chép API key hoặc header của yêu cầu.
    details = {}
    allowed_fields = ('source', 'threats', 'checked_at', 'message')
    for field in allowed_fields:
        if field in result:
            details[field] = result[field]
    return _save('link', url, result['status'], details=details, db_path=db_path)


def _filters(kind=None, status=None, search=''):
    """Trả về (phần WHERE của SQL, danh sách giá trị tương ứng)."""
    clauses = []
    values = []
    if kind:
        clauses.append('kind = ?')
        values.append(kind)
    if status:
        clauses.append('status = ?')
        values.append(status)
    if search:
        clauses.append('instr(casefold(content), ?) > 0')
        values.append(search.casefold())
    if clauses:
        where = ' WHERE ' + ' AND '.join(clauses)
    else:
        where = ''
    return where, values


def list_history(*, kind=None, status=None, search='', limit=20, offset=0, db_path=None):
    """Trả về (các bản ghi của trang hiện tại, tổng số bản ghi khớp bộ lọc)."""
    if not 1 <= limit <= 200 or offset < 0:
        raise ValueError('Giới hạn hoặc vị trí trang không hợp lệ.')
    if not database_path(db_path).exists():
        return [], 0
    where, values = _filters(kind, status, search)
    with connect(db_path) as db:
        count_sql = 'SELECT count(*) FROM history' + where
        total_row = db.execute(count_sql, values).fetchone()
        total = total_row[0]

        select_sql = 'SELECT * FROM history' + where
        select_sql += ' ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?'
        page_values = values + [limit, offset]
        rows = db.execute(select_sql, page_values).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item['details'] = json.loads(item['details'])
        result.append(item)
    return result, total


def delete_history(record_id=None, *, db_path=None):
    """Xóa theo ID, hoặc toàn bộ nếu không có ID. Trả về số lượt đã xóa."""
    if not database_path(db_path).exists():
        return 0
    with connect(db_path) as db:
        if record_id is None:
            return db.execute('DELETE FROM history').rowcount
        return db.execute('DELETE FROM history WHERE id = ?', (record_id,)).rowcount

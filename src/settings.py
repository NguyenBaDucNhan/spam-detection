"""Đọc cấu hình và tìm đường dẫn từ thư mục gốc project."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent

def load_config():
    """Trả về nội dung configs/app.json dưới dạng dictionary."""
    config_path = ROOT / 'configs' / 'app.json'
    config_text = config_path.read_text(encoding='utf-8')
    config = json.loads(config_text)
    return config

def project_path(value):
    """Giữ đường dẫn tuyệt đối; ghép đường dẫn tương đối với gốc project."""
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path

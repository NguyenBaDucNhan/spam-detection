"""Làm sạch văn bản theo đúng cách đã dùng khi huấn luyện model có sẵn."""
import re

MAX_TEXT_LENGTH = 20000

def clean_text(text: str) -> str:
    """Nhận chuỗi và trả về chuỗi chữ thường, không có khoảng trắng thừa."""
    if not isinstance(text, str):
        raise ValueError("Nội dung phải là văn bản.")
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text

def validate_text(text: str) -> str:
    """Kiểm tra đầu vào trước khi đưa vào model; lỗi được hiển thị cho người dùng."""
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Vui lòng nhập nội dung tin nhắn.")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Tin nhắn dài tối đa {MAX_TEXT_LENGTH:,} ký tự.")
    return cleaned

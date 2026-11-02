"""Tìm dấu hiệu bằng quy tắc; kết quả này độc lập với dự đoán của SVM."""
import re
import unicodedata
from .link_check import extract_urls

def fold(text):
    """Bỏ dấu để cùng một quy tắc dùng được cho cả chữ có dấu và không dấu."""
    text = unicodedata.normalize('NFD', text.lower().replace('đ', 'd'))
    characters = []
    for character in text:
        if not unicodedata.combining(character):
            characters.append(character)
    text_without_accents = ''.join(characters)
    return re.sub(r"\s+", " ", text_without_accents)

RULES = [
    ('otp', 'Có nhắc đến OTP hoặc thông tin đăng nhập',
     r'\b(otp|mat khau|ma xac thuc|password|verification code)\b',
     'Không cung cấp OTP hoặc mật khẩu cho người khác; tin thông báo OTP hợp lệ cũng có thể chứa các từ này.'),
    ('urgency', 'Có ngôn ngữ thúc giục hoặc đe dọa',
     r'\b(khan cap|ngay lap tuc|bi khoa|trong \d+ (gio|phut)|urgent|immediately)\b',
     'Dừng lại và kiểm tra yêu cầu qua kênh chính thức trước khi thao tác.'),
    ('money', 'Có nhắc đến chuyển tiền hoặc khoản phí',
     r'\b(chuyen khoan|chuyen tien|nop phi|dong phi|transfer money|wire transfer)\b',
     'Xác minh người nhận và mục đích thanh toán qua một kênh độc lập.'),
    ('prize', 'Có lời mời nhận thưởng hoặc quà',
     r'\b(trung thuong|nhan thuong|nhan qua|won a prize|claim your prize|winner)\b',
     'Kiểm tra nguồn chương trình; không chuyển phí chỉ để nhận quà.'),
]

def analyze_indicators(text):
    """Mỗi quy tắc khớp tạo một dictionary trong danh sách trả về."""
    normalized = fold(text)
    findings = []
    for code, title, pattern, advice in RULES:
        match = re.search(pattern, normalized)
        if match:
            finding = {
                'code': code,
                'title': title,
                'evidence': match.group(),
                'advice': advice,
            }
            findings.append(finding)
    urls = extract_urls(text)
    if urls:
        finding = {
            'code': 'url',
            'title': 'Tin nhắn có đường link',
            'evidence': ' | '.join(urls),
            'advice': 'Xem mục Kiểm tra đường link để phân tích cấu trúc hoặc chủ động tra cứu cảnh báo trực tuyến.',
        }
        findings.append(finding)
    return findings

"""Đọc chữ bằng Tesseract trên máy. Truyền ảnh qua stdin, không gọi mạng."""
from dataclasses import dataclass
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from .settings import ROOT

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 16_000_000
TESSDATA = ROOT / 'models' / 'ocr'
LANGUAGES = {'vie+eng': ('vie', 'eng'), 'vie': ('vie',), 'eng': ('eng',)}


class OCRError(ValueError):
    """Lỗi có thông báo để giao diện hướng dẫn người dùng xử lý."""


@dataclass
class OCRResult:
    """Kết quả gồm văn bản, ngôn ngữ và kích thước ảnh đã xử lý."""
    text: str
    language: str
    width: int
    height: int


def find_tesseract():
    """Tìm lần lượt trong TESSERACT_CMD, PATH và hai vị trí cài Windows phổ biến."""
    configured = os.environ.get('TESSERACT_CMD')
    if configured:
        path = shutil.which(configured)
        if path:
            return path
        raise OCRError('TESSERACT_CMD chưa trỏ đến tesseract.exe hợp lệ. Xem OCR_SETUP.md.')
    path = shutil.which('tesseract')
    if path:
        return path
    # Kiểm tra vị trí cài Windows để không bắt buộc người dùng sửa PATH.
    for base in (os.environ.get('ProgramFiles'), os.environ.get('LOCALAPPDATA')):
        if base:
            candidate = Path(base) / 'Tesseract-OCR' / 'tesseract.exe'
            if candidate.is_file():
                return str(candidate)
    raise OCRError('Chưa tìm thấy Tesseract OCR. Cài Tesseract theo OCR_SETUP.md rồi mở lại ứng dụng. Chức năng nhập văn bản vẫn dùng được.')


def prepare_image(data):
    """Trả về ảnh Pillow đã chuẩn hóa, giữ nguyên các bước xử lý của bản trước."""
    if not data:
        raise OCRError('Ảnh tải lên đang rỗng.')
    if len(data) > MAX_UPLOAD_BYTES:
        raise OCRError('Vui lòng chọn ảnh không quá 8 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as original:
                if original.format not in ('PNG', 'JPEG', 'WEBP'):
                    raise OCRError('Chỉ hỗ trợ ảnh PNG, JPG/JPEG hoặc WebP.')
                if original.width * original.height > MAX_PIXELS:
                    raise OCRError('Ảnh quá lớn. Hãy cắt vùng tin nhắn hoặc dùng ảnh tối đa 16 triệu điểm ảnh.')
                original.load()
                image = ImageOps.exif_transpose(original).convert('RGBA')
        # Ghép nền trắng trước khi chuyển ảnh trong suốt sang thang xám.
        white = Image.new('RGBA', image.size, 'white')
        white.alpha_composite(image)
        image = white.convert('L')
        # Thu nhỏ ảnh lớn và phóng ảnh nhỏ; giữ nguyên ngưỡng và phép nội suy.
        image.thumbnail((2400, 3200), Image.Resampling.LANCZOS)
        if max(image.size) < 1600:
            scale = min(2.0, 1600 / max(image.size))
            new_width = max(1, round(image.width * scale))
            new_height = max(1, round(image.height * scale))
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Ước lượng nền tối bằng bốn góc ảnh rồi đảo màu nếu cần.
        border = [image.getpixel((0, 0)), image.getpixel((image.width-1, 0)),
                  image.getpixel((0, image.height-1)), image.getpixel((image.width-1, image.height-1))]
        if sum(border) / len(border) < 100:
            image = ImageOps.invert(image)
        image = ImageOps.expand(ImageOps.autocontrast(image), border=20, fill='white')
        return image
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise OCRError('Không đọc được ảnh. Hãy tải ảnh PNG/JPG/WebP hợp lệ, rõ chữ và có kích thước nhỏ hơn.') from exc


def extract_text(data, language='vie+eng', *, timeout=30):
    """Chuẩn bị ảnh, chạy Tesseract và trả về OCRResult; không tự phân loại spam."""
    if language not in LANGUAGES:
        raise OCRError('Ngôn ngữ OCR không hợp lệ.')
    image = prepare_image(data)
    executable = find_tesseract()
    missing = []
    for lang in LANGUAGES[language]:
        language_file = TESSDATA / f'{lang}.traineddata'
        if not language_file.is_file():
            missing.append(lang)
    if missing:
        raise OCRError('Thiếu dữ liệu ngôn ngữ OCR: ' + ', '.join(missing) + '. Hãy giải nén lại đầy đủ thư mục models/ocr/.')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    command = [executable, 'stdin', 'stdout', '--tessdata-dir', str(TESSDATA),
               '-l', language, '--oem', '1', '--psm', '6']
    # Giữ cửa sổ Tesseract ẩn khi chạy trên Windows.
    if os.name == 'nt':
        creation_flags = subprocess.CREATE_NO_WINDOW
    else:
        creation_flags = 0
    try:
        result = subprocess.run(command, input=buffer.getvalue(), capture_output=True,
                                timeout=timeout, check=False,
                                creationflags=creation_flags)
    except subprocess.TimeoutExpired as exc:
        raise OCRError('OCR quá thời gian xử lý. Hãy cắt ảnh chỉ còn vùng tin nhắn rồi thử lại.') from exc
    except OSError as exc:
        raise OCRError('Không chạy được Tesseract. Kiểm tra cài đặt theo OCR_SETUP.md.') from exc
    if result.returncode:
        raise OCRError('Tesseract không đọc được ảnh. Kiểm tra bản Tesseract 5 và thư mục models/ocr/, hoặc thử ảnh khác.')
    text = result.stdout.decode('utf-8', errors='replace').strip()
    if not text:
        raise OCRError('Chưa đọc được chữ trong ảnh. Hãy cắt sát vùng tin nhắn, chọn ảnh rõ hơn hoặc nhập nội dung thủ công.')
    return OCRResult(text=text, language=language, width=image.width, height=image.height)

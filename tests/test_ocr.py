from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from src.ocr import (extract_text, prepare_image, find_tesseract,
                     OCRError, MAX_UPLOAD_BYTES, TESSDATA)


def image_bytes(text='Hello spam test', dark=False):
    image = Image.new('RGB', (1000, 160), 'black' if dark else 'white')
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 38)
    except OSError:
        font = ImageFont.load_default(size=38)
    ImageDraw.Draw(image).text((30, 50), text, font=font, fill='white' if dark else 'black')
    data = BytesIO()
    image.save(data, format='PNG')
    return data.getvalue()


class OCRTests(unittest.TestCase):
    def test_empty_invalid_and_oversized_images(self):
        for data in (b'', b'not an image', b'x'*(MAX_UPLOAD_BYTES+1)):
            with self.subTest(size=len(data)), self.assertRaises(OCRError):
                prepare_image(data)

    def test_pixel_limit(self):
        image = Image.new('1', (5000, 4000))
        out = BytesIO()
        image.save(out, format='PNG')
        with self.assertRaisesRegex(OCRError, 'quá lớn'):
            prepare_image(out.getvalue())

    def test_dark_background_is_inverted(self):
        prepared = prepare_image(image_bytes(dark=True))
        self.assertEqual(prepared.mode, 'L')
        self.assertGreater(prepared.getpixel((25, 25)), 200)

    def test_missing_engine_has_actionable_error(self):
        with patch.dict('os.environ', {'TESSERACT_CMD':'/no/such/tesseract'}):
            with self.assertRaisesRegex(OCRError, 'TESSERACT_CMD'):
                find_tesseract()

    def test_timeout_and_blank_output(self):
        data = image_bytes()
        with patch('src.ocr.find_tesseract', return_value='tesseract'):
            with patch('src.ocr.subprocess.run', side_effect=subprocess.TimeoutExpired('tesseract', 1)):
                with self.assertRaisesRegex(OCRError, 'quá thời gian'):
                    extract_text(data)
            with patch('src.ocr.subprocess.run', return_value=subprocess.CompletedProcess([],0,b'  ',b'')):
                with self.assertRaisesRegex(OCRError, 'Chưa đọc được chữ'):
                    extract_text(data)

    @unittest.skipUnless(shutil.which('tesseract'), 'Cần cài Tesseract để chạy integration test')
    def test_real_engine_english_and_vietnamese(self):
        result = extract_text(image_bytes(), 'eng')
        self.assertIn('hello', result.text.lower())
        fixture = Path(__file__).resolve().parent.parent/'examples'/'ocr_demo_vi.png'
        result_vi = extract_text(fixture.read_bytes(), 'vie+eng')
        self.assertIn('chuyển khoản', result_vi.text.lower())


if __name__ == '__main__':
    unittest.main()

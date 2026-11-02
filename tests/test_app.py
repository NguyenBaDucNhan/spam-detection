"""Streamlit UI flow test; does not persist real feedback or contact a service."""
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from io import BytesIO
from PIL import Image
from src.ocr import OCRResult, OCRError
import tempfile
from src.history import list_history

ROOT = Path(__file__).resolve().parent.parent


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db_path = str(Path(self.temporary.name) / 'history.sqlite3')
        self.env = patch.dict('os.environ', {'SPAM_HISTORY_DB': self.db_path})
        self.env.start()
        self.addCleanup(self.env.stop)

    def new_app(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=20).run()
        self.assertFalse(app.exception)
        return app

    def click(self, app, label):
        next(b for b in app.button if b.label == label).click().run()
        self.assertFalse(app.exception)

    def test_prediction_feedback_and_stale_input(self):
        app = self.new_app()
        app.text_area[0].set_value('Bạn đã trúng thưởng. Chuyển khoản phí ngay lập tức.').run()
        self.click(app, 'Kiểm tra tin nhắn')
        self.assertIn('result', app.session_state)
        self.assertTrue(app.radio)
        with patch('src.feedback.save_feedback', return_value='test-id') as save:
            self.click(app, 'Gửi phản hồi')
            save.assert_called_once()
            self.assertFalse(save.call_args.kwargs['save_text'])
        self.assertTrue(app.session_state.feedback_saved)
        app.text_area[0].set_value('Nội dung mới').run()
        self.assertFalse(app.radio)
        self.assertTrue(any('đã thay đổi' in i.value for i in app.info))

    def test_empty_input_and_consent(self):
        app = self.new_app()
        self.click(app, 'Kiểm tra tin nhắn')
        self.assertTrue(app.warning)
        app.text_area[0].set_value('Mai mình gặp nhau lúc 8 giờ nhé.').run()
        self.click(app, 'Kiểm tra tin nhắn')
        next(x for x in app.checkbox if x.key == 'consent_text').check()
        with patch('src.feedback.save_feedback', return_value='test-id') as save:
            self.click(app, 'Gửi phản hồi')
            self.assertTrue(save.call_args.kwargs['save_text'])

    def test_ocr_fills_editable_text_then_predicts(self):
        data = BytesIO()
        Image.new('RGB', (200, 100), 'white').save(data, format='PNG')
        recognized = 'Văn bản do OCR đọc được'
        with patch('streamlit.file_uploader', return_value=data), patch('src.ocr.extract_text', return_value=OCRResult(recognized, 'vie+eng', 200, 100)):
            app = self.new_app()
            self.click(app, 'Trích xuất chữ từ ảnh')
            self.assertEqual(app.text_area[0].value, recognized)
            self.assertNotIn('result', app.session_state)
            app.text_area[0].set_value('Nội dung người dùng sửa lại').run()
            self.click(app, 'Kiểm tra tin nhắn')
            self.assertEqual(app.session_state.result['text'], 'Nội dung người dùng sửa lại')

    def test_ocr_error_keeps_existing_text(self):
        data = BytesIO()
        Image.new('RGB', (200, 100), 'white').save(data, format='PNG')
        with patch('streamlit.file_uploader', return_value=data), patch('src.ocr.extract_text', side_effect=OCRError('Chưa tìm thấy Tesseract')):
            app = self.new_app()
            app.text_area[0].set_value('Giữ nội dung đang nhập').run()
            self.click(app, 'Trích xuất chữ từ ảnh')
            self.assertEqual(app.text_area[0].value, 'Giữ nội dung đang nhập')
            self.assertTrue(any('Tesseract' in x.value for x in app.warning))

    def test_link_lookup_is_explicit_and_stale_results_cleared(self):
        with patch('src.link_check.lookup_url', return_value={
            'status':'no_match', 'checked_at':'2026-11-02T00:00:00+00:00'}) as lookup:
            app = self.new_app()
            app.text_area[0].set_value('Xem https://example.com/AbC').run()
            lookup.assert_not_called()
            next(x for x in app.text_input if x.key == 'safe_browsing_key').set_value('test-key').run()
            lookup.assert_not_called()
            self.click(app, 'Tra cứu link 1')
            lookup.assert_called_once_with('https://example.com/AbC', 'test-key')
            self.assertTrue(any('Không có nghĩa link an toàn' in x.value for x in app.info))
            app.text_area[0].set_value('https://example.org/new').run()
            self.assertFalse(app.session_state.link_results)

    def test_link_without_key_never_looks_up(self):
        with patch.dict('os.environ', {'SAFE_BROWSING_API_KEY':''}), patch('src.link_check.lookup_url') as lookup:
            app = self.new_app()
            app.text_area[0].set_value('https://example.com').run()
            self.assertTrue(next(b for b in app.button if b.label == 'Tra cứu link 1').disabled)
            self.click(app, 'Kiểm tra tin nhắn')
            lookup.assert_not_called()

    def test_history_persists_across_sessions_without_rerun_duplicates(self):
        app = self.new_app()
        app.text_area[0].set_value('Mai mình gặp nhau lúc 8 giờ nhé.').run()
        self.click(app, 'Kiểm tra tin nhắn')
        rows, total = list_history(db_path=self.db_path)
        self.assertEqual(total, 1)
        self.assertEqual(rows[0]['kind'], 'message')
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(list_history(db_path=self.db_path)[1], 1)
        other = self.new_app()
        self.assertTrue(any(rows[0]['content'] in item.value for item in other.code))

    def test_history_toggle_and_confirmed_delete(self):
        app = self.new_app()
        next(x for x in app.checkbox if x.key == 'save_history').uncheck().run()
        app.text_area[0].set_value('Mai mình gặp nhau lúc 8 giờ nhé.').run()
        self.click(app, 'Kiểm tra tin nhắn')
        self.assertEqual(list_history(db_path=self.db_path)[1], 0)
        next(x for x in app.checkbox if x.key == 'save_history').check().run()
        self.click(app, 'Kiểm tra tin nhắn')
        self.assertEqual(list_history(db_path=self.db_path)[1], 1)
        self.click(app, 'Xóa toàn bộ lịch sử')
        self.assertEqual(list_history(db_path=self.db_path)[1], 1)
        next(x for x in app.checkbox if x.key == 'confirm_clear_history').check()
        self.click(app, 'Xóa toàn bộ lịch sử')
        self.assertEqual(list_history(db_path=self.db_path)[1], 0)

    def test_link_click_creates_exactly_one_history_record(self):
        with patch('src.link_check.lookup_url', return_value={
            'status':'danger', 'source':'Google Safe Browsing', 'threats':['MALWARE']}) as lookup:
            app = self.new_app()
            app.text_area[0].set_value('https://example.com/').run()
            next(x for x in app.text_input if x.key == 'safe_browsing_key').set_value('never-save-this-key').run()
            self.click(app, 'Tra cứu link 1')
            app.run()
            self.assertFalse(app.exception)
            rows, total = list_history(db_path=self.db_path)
            self.assertEqual(total, 1)
            self.assertEqual(rows[0]['status'], 'danger')
            self.assertNotIn('never-save-this-key', str(rows))

    def test_history_storage_error_does_not_break_prediction(self):
        app = self.new_app()
        app.text_area[0].set_value('Mai mình gặp nhau lúc 8 giờ nhé.').run()
        with patch('src.history.save_message', side_effect=OSError('no permission')):
            self.click(app, 'Kiểm tra tin nhắn')
            self.assertIn('result', app.session_state)
            self.assertTrue(any('chưa lưu được lịch sử' in item.value for item in app.warning))


if __name__ == '__main__':
    unittest.main()

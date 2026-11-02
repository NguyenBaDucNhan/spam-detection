import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.preprocessing import clean_text, validate_text
from src.predictor import SpamPredictor
from src.indicators import analyze_indicators
from src.feedback import save_feedback
from src.dataset import load_dataset, split_dataset, template_key
from src.evaluate import metrics


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = SpamPredictor()

    def test_preprocessing_keeps_vietnamese_and_links(self):
        self.assertEqual(clean_text('  CHÀO\n bạn https://ABC.vn  '), 'chào bạn https://abc.vn')

    def test_invalid_input_rejected(self):
        for value in ('  \n ', 'a' * 20001, None):
            with self.subTest(value=str(value)[:10]), self.assertRaises(ValueError):
                self.predictor.predict(value)

    def test_bundled_pipeline_and_shared_cleaning(self):
        message = '  Mai MÌNH gặp nhau lúc 8 giờ nhé.\n'
        actual = self.predictor.predict(message)
        self.assertEqual(actual.label, self.predictor.model.predict([clean_text(message)])[0])
        self.assertAlmostEqual(actual.score, float(self.predictor.model.decision_function([clean_text(message)])[0]))
        self.assertIn(actual.label, ('ham', 'spam'))

    def test_indicators_accented_unaccented_and_url_deduplication(self):
        message = 'CHUYỂN KHOẢN ngay lập tức https://test.example. https://test.example'
        found = {item['code']:item for item in analyze_indicators(message)}
        self.assertTrue({'money','urgency','url'}.issubset(found))
        self.assertEqual(found['url']['evidence'], 'https://test.example')
        self.assertIn('otp', {i['code'] for i in analyze_indicators('Ma xac thuc la 123456')})

    def test_feedback_default_omits_text_and_opt_in_saves_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'feedback.sqlite3'
            text = 'Tin nhắn riêng tư'
            result = self.predictor.predict(text)
            save_feedback(text, result, 'ham', db_path=path)
            save_feedback(text, result, 'spam', save_text=True, db_path=path)
            with sqlite3.connect(path) as db:
                values = db.execute('SELECT message, actual_label FROM feedback ORDER BY rowid').fetchall()
            self.assertEqual(values, [(None, 'ham'), (text, 'spam')])
            with self.assertRaises(ValueError):
                save_feedback(text, result, 'other', db_path=path)

    def test_data_has_no_exact_duplicates_or_template_leakage(self):
        df = load_dataset()
        self.assertEqual(len(df), df['message'].nunique())
        self.assertEqual(set(df['label']), {'ham', 'spam'})
        train, test = split_dataset(df)
        self.assertFalse(set(train.message.map(template_key)) & set(test.message.map(template_key)))
        self.assertEqual(len(train)+len(test),len(df))

    def test_metrics_confusion_orientation(self):
        actual = ['ham','ham','ham','spam','spam','spam']
        predicted = ['ham','ham','spam','ham','spam','spam']
        report = metrics(actual, predicted)
        self.assertEqual(report['confusion_matrix_ham_spam'], [[2,1],[1,2]])
        self.assertAlmostEqual(report['spam_precision'], 2/3)
        self.assertAlmostEqual(report['spam_recall'], 2/3)


if __name__ == '__main__':
    unittest.main()

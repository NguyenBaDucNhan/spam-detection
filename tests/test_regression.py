"""So sánh với kết quả ghi lại từ bản trước khi viết lại code."""
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import unittest

from src.dataset import load_dataset
from src.indicators import analyze_indicators
from src.predictor import SpamPredictor


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'before_refactor.json'


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
        cls.predictor = SpamPredictor()

    def test_original_function_parameters_are_unchanged(self):
        for name, functions in self.expected['signatures'].items():
            module = importlib.import_module('src.' + name)
            for function_name, old_signature in functions.items():
                value = module
                for part in function_name.split('.'):
                    value = getattr(value, part)
                with self.subTest(module=name, function=function_name):
                    self.assertEqual(str(inspect.signature(value)), old_signature)

    def test_original_predictions_indicators_and_errors_are_unchanged(self):
        texts = self.expected['texts']
        for index, text in enumerate(texts):
            with self.subTest(text=text):
                self.assertEqual(analyze_indicators(text), self.expected['indicators'][index])
                try:
                    actual = self.predictor.predict(text).to_dict()
                except Exception as error:
                    actual = {'exception':type(error).__name__, 'message':str(error)}
                self.assertEqual(actual, self.expected['predictions'][index])

    def test_labels_and_scores_on_all_original_training_messages_are_unchanged(self):
        data = load_dataset()
        outputs = {
            'labels': self.predictor.model.predict(data.message).tolist(),
            'scores': self.predictor.model.decision_function(data.message).tolist(),
        }
        encoded = json.dumps(outputs, sort_keys=True).encode()
        actual_hash = hashlib.sha256(encoded).hexdigest()
        self.assertEqual(actual_hash, self.expected['full_dataset_output_hash'])


if __name__ == '__main__':
    unittest.main()

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from src.history import save_message, save_link, list_history, delete_history


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'history.sqlite3'
        self.prediction = SimpleNamespace(label='spam', score=0.5, model_id='test-model', indicators=[])

    def test_empty_history_does_not_create_database(self):
        self.assertEqual(list_history(db_path=self.path), ([], 0))
        self.assertFalse(self.path.exists())

    def test_persistence_unicode_filter_pagination_and_single_delete(self):
        first = save_message('ĐẦU TƯ được không?', self.prediction, db_path=self.path)
        second = save_message('Một tin khác', self.prediction, db_path=self.path)
        rows, total = list_history(db_path=self.path, limit=1)
        self.assertEqual(total, 2)
        self.assertEqual(rows[0]['id'], second)
        self.assertEqual(rows[0]['score'], 0.5)
        rows, _ = list_history(db_path=self.path, limit=1, offset=1)
        self.assertEqual(rows[0]['id'], first)
        rows, total = list_history(search='đầu tư', db_path=self.path)
        self.assertEqual(total, 1)
        self.assertEqual(rows[0]['id'], first)
        self.assertEqual(delete_history(first, db_path=self.path), 1)
        self.assertEqual(list_history(db_path=self.path)[1], 1)

    def test_link_metadata_allowlist_and_filters(self):
        save_message('Tin nhắn', self.prediction, db_path=self.path)
        save_link('https://example.com/', {'status':'no_match', 'source':'Google Safe Browsing',
                  'api_key':'secret-key', 'headers':{'Authorization':'secret'}}, db_path=self.path)
        rows, total = list_history(kind='link', status='no_match', db_path=self.path)
        self.assertEqual(total, 1)
        self.assertNotIn('secret', str(rows))
        self.assertEqual(rows[0]['details'], {'source':'Google Safe Browsing'})
        self.assertEqual(list_history(status='danger', db_path=self.path)[1], 0)

    def test_delete_all_and_parameterized_search(self):
        save_message("x' OR 1=1 --", self.prediction, db_path=self.path)
        self.assertEqual(list_history(search="' OR", db_path=self.path)[1], 1)
        self.assertEqual(delete_history("' OR 1=1 --", db_path=self.path), 0)
        self.assertEqual(delete_history(db_path=self.path), 1)
        self.assertEqual(list_history(db_path=self.path)[1], 0)


if __name__ == '__main__':
    unittest.main()

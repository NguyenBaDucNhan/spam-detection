from io import BytesIO
import json
import unittest
from unittest.mock import patch
from urllib import error

from src.link_check import extract_urls, analyze_url, lookup_url, LinkCheckError


class LinkTests(unittest.TestCase):
    def fake_response(self, data):
        return BytesIO(json.dumps(data).encode())

    def test_extraction_deduplicates_keeps_balanced_parentheses_and_ignores_email(self):
        text = 'Xem (https://example.com/a(b)). www.example.org và example.net/path. a@example.edu https://example.com/a(b)'
        self.assertEqual(extract_urls(text), ['https://example.com/a(b)', 'www.example.org', 'example.net/path'])

    def test_normalization_preserves_query_and_path_case(self):
        result = analyze_url('HTTP://Example.COM/AbC?Token=Aa#private')
        self.assertEqual(result['url'], 'http://example.com/AbC?Token=Aa')
        self.assertTrue(result['eligible'])
        self.assertTrue(result['warnings'])

    def test_structural_warnings_are_not_remote_verdicts(self):
        self.assertTrue(analyze_url('https://bit.ly/AbC')['warnings'])
        self.assertTrue(analyze_url('https://xn--bcher-kva.de')['warnings'])
        self.assertFalse(analyze_url('https://example.com')['warnings'])
        self.assertNotIn('status', analyze_url('https://example.com'))

    def test_invalid_private_and_credential_urls_not_sent(self):
        for url in ['http://127.0.0.1', 'http://[::1]/', 'http://10.0.0.1',
                    'http://localhost', 'https://host.local', 'https://user:secret@example.com',
                    'ftp://example.com/a', 'https://example.com:99999', 'https://x.example',
                    'https://example.com\\@evil.com', 'https://bad_host.com']:
            with self.subTest(url=url), patch('src.link_check.request.build_opener') as build:
                self.assertFalse(analyze_url(url)['eligible'])
                with self.assertRaises(LinkCheckError):
                    lookup_url(url, 'key')
                build.assert_not_called()

    def test_no_key_means_no_network_request(self):
        with patch('src.link_check.request.build_opener') as build:
            with self.assertRaisesRegex(LinkCheckError, 'Chưa có API key'):
                lookup_url('https://example.com', '')
            build.assert_not_called()

    def test_lookup_only_calls_fixed_google_endpoint_and_no_match_is_not_safe(self):
        with patch('src.link_check.request.build_opener') as build:
            build.return_value.open.return_value = self.fake_response({})
            result = lookup_url('https://example.com/Path?q=A#fragment', 'key')
            req = build.return_value.open.call_args.args[0]
            self.assertTrue(req.full_url.startswith('https://safebrowsing.googleapis.com/'))
            submitted = json.loads(req.data)
            self.assertEqual(submitted['threatInfo']['threatEntries'], [{'url':'https://example.com/Path?q=A'}])
            self.assertEqual(result['status'], 'no_match')

    def test_match_is_a_warning(self):
        with patch('src.link_check.request.build_opener') as build:
            build.return_value.open.return_value = self.fake_response({'matches':[
                {'threatType':'SOCIAL_ENGINEERING','threat':{'url':'https://example.com/'}}]})
            result = lookup_url('https://example.com', 'key')
            self.assertEqual(result['status'], 'danger')
            self.assertEqual(result['threats'], ['SOCIAL_ENGINEERING'])

    def test_errors_never_report_no_match_or_expose_key(self):
        for failure in [error.HTTPError('secret-key-in-url',403,'secret',None,None),
                        error.HTTPError('secret-key-in-url',429,'secret',None,None),
                        error.URLError('secret-key-in-url'), TimeoutError('secret-key-in-url')]:
            with self.subTest(failure=str(type(failure))), patch('src.link_check.request.build_opener') as build:
                build.return_value.open.side_effect = failure
                with self.assertRaises(LinkCheckError) as caught:
                    lookup_url('https://example.com', 'secret-key-in-url')
                self.assertNotIn('secret', str(caught.exception))

    def test_bad_api_responses_fail_closed(self):
        for data in [{'matches':'invalid'}, {'error':'failure'}, ['bad'], {'unknown':'failure'}, {'matches':[{}]}]:
            with self.subTest(data=data), patch('src.link_check.request.build_opener') as build:
                build.return_value.open.return_value = self.fake_response(data)
                with self.assertRaises(LinkCheckError):
                    lookup_url('https://example.com', 'key')


if __name__ == '__main__':
    unittest.main()

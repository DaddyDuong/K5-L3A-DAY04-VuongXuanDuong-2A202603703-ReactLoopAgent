"""Phục hồi body JSON hỏng phải hữu hạn và không lộ nội dung response."""
import io
import json
import unittest
from contextlib import redirect_stderr
from unittest.mock import MagicMock, patch

from providers import post_json


def response(body):
    context = MagicMock()
    context.__enter__.return_value = io.StringIO(body)
    return context


class TransportTests(unittest.TestCase):
    @patch('providers.time.sleep')
    @patch('providers.urllib.request.urlopen')
    def test_invalid_json_then_success_keeps_request_and_endpoint(self, urlopen, sleep):
        urlopen.side_effect = [response('invalid-private-data'), response('{"choices": []}')]
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = post_json('https://example.invalid', {}, {'model': 'test'})
        self.assertEqual(result, {'choices': []})
        self.assertEqual(urlopen.call_count, 2)
        self.assertIs(urlopen.call_args_list[0].args[0], urlopen.call_args_list[1].args[0])
        sleep.assert_called_once_with(1)
        self.assertNotIn('invalid-private-data', stderr.getvalue())

    @patch('providers.time.sleep')
    @patch('providers.urllib.request.urlopen')
    def test_persistent_invalid_json_stops(self, urlopen, sleep):
        urlopen.side_effect = [response('') for _ in range(3)]
        with redirect_stderr(io.StringIO()), self.assertRaises(json.JSONDecodeError):
            post_json('https://example.invalid', {}, {})
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])


if __name__ == '__main__':
    unittest.main()

"""Kiểm tra lỗi giao thức và phục hồi observation bằng provider giả."""
import json
import unittest

from agent import run_agent
from status_tools import StatusTools
from test_lab import FakeProvider, final, tool_call


class RobustnessTests(unittest.TestCase):
    def test_provider_exception_does_not_leak_message(self):
        class BrokenProvider:
            def complete(self, messages, schemas):
                raise RuntimeError('private-account-secret')
        result = run_agent('Kiểm tra', BrokenProvider(), StatusTools())
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['trace'][-1]['event'], 'provider_error')
        self.assertNotIn('private-account-secret', json.dumps(result))

    def test_non_object_json_is_observation(self):
        for arguments in ('[]', 'null', '42'):
            with self.subTest(arguments=arguments):
                provider = FakeProvider([tool_call('bad', 'get_status', arguments), final()])
                result = run_agent('Kiểm tra', provider, StatusTools())
                self.assertEqual(result['status'], 'completed')
                observation = provider.histories[1][-1]
                self.assertEqual(observation['tool_call_id'], 'bad')
                self.assertEqual(json.loads(observation['content'])['error'], 'INVALID_ARGUMENTS')

    def test_unexpected_tool_exception_returns_observation(self):
        class BrokenTools:
            def execute(self, name, arguments):
                raise RuntimeError('private-account-secret')
        provider = FakeProvider([tool_call('t1', 'get_status', '{}'), final()])
        result = run_agent('Kiểm tra', provider, BrokenTools())
        self.assertEqual(result['status'], 'completed')
        observation = provider.histories[1][-1]
        self.assertEqual(observation['tool_call_id'], 't1')
        self.assertEqual(json.loads(observation['content'])['error'], 'RuntimeError')
        self.assertNotIn('private-account-secret', json.dumps(result))

    def test_malformed_provider_response_is_error(self):
        for response in ({}, None, {'message': {}, 'calls': 'bad', 'finish': 'stop'}):
            with self.subTest(response=response):
                result = run_agent('Kiểm tra', FakeProvider([response]), StatusTools())
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['trace'][-1]['event'], 'provider_error')

    def test_invalid_step_budget_is_error(self):
        for budget in (0, -1, True, 1.5):
            with self.subTest(budget=budget):
                result = run_agent('Kiểm tra', FakeProvider([]), StatusTools(), budget)
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['usage'], [])


if __name__ == '__main__':
    unittest.main()

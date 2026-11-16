import unittest
from src.agent.analyst import analyst_agent

class TestAgent(unittest.TestCase):
    def test_strict_json_detection(self):
        query_eval = 'What is the sum? Reply with ONLY this JSON: {"answer": <number>, "log_url": "..."}'
        self.assertTrue(analyst_agent.is_strict_json_request(query_eval))

        query_normal = "Can you help me analyze this dataset and plot a chart?"
        self.assertFalse(analyst_agent.is_strict_json_request(query_normal))

    def test_json_cleaner_and_log_injection(self):
        raw_model_output = '```json\n{"answer": 42}\n```'
        cleaned = analyst_agent.clean_json_output(raw_model_output, "http://localhost:8000/run.jsonl")
        self.assertIn('"log_url": "http://localhost:8000/run.jsonl"', cleaned)
        self.assertIn('"answer": 42', cleaned)

if __name__ == "__main__":
    unittest.main()

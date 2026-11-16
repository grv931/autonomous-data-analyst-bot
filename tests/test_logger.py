import os
import unittest
import tempfile
from src.storage.logger import AuditLogger

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.temp_file.close()
        self.logger = AuditLogger(log_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_log_and_retrieve(self):
        self.logger.log(
            event_type="test_event",
            chat_id="user_123",
            user_message="Hello data bot",
            answer='{"answer": 42}',
            duration_ms=120.5,
        )

        logs = self.logger.get_recent_logs(limit=10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["chat_id"], "user_123")
        self.assertEqual(logs[0]["user_message"], "Hello data bot")

        stats = self.logger.get_stats()
        self.assertEqual(stats["total_queries"], 1)
        self.assertEqual(stats["errors"], 0)
        self.assertEqual(stats["success_rate"], 100.0)

if __name__ == "__main__":
    unittest.main()

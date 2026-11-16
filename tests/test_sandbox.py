import unittest
import pandas as pd
from src.engine.sandbox import sandbox

class TestSandbox(unittest.TestCase):
    def test_basic_computation(self):
        code = "result = 15 * 20"
        res = sandbox.execute(code, chat_id="test_chat")
        self.assertTrue(res.success)
        self.assertEqual(res.output_value, 300)

    def test_dataframe_execution(self):
        df = pd.DataFrame({
            "product": ["A", "B", "A", "B"],
            "revenue": [100, 200, 150, 300]
        })
        code = "result = int(df.groupby('product')['revenue'].sum()['B'])"
        res = sandbox.execute(code, chat_id="test_chat", df=df)
        self.assertTrue(res.success)
        self.assertEqual(res.output_value, 500)

    def test_chart_generation(self):
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        code = "plt.plot(df['x'], df['y']); plt.title('Test Plot')"
        res = sandbox.execute(code, chat_id="test_chat", df=df)
        self.assertTrue(res.success)
        self.assertIsNotNone(res.chart_bytes)
        self.assertGreater(len(res.chart_bytes), 1000)

    def test_error_handling(self):
        code = "result = 10 / 0"
        res = sandbox.execute(code, chat_id="test_chat")
        self.assertFalse(res.success)
        self.assertIn("ZeroDivisionError", res.error)

if __name__ == "__main__":
    unittest.main()

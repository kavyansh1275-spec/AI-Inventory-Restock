import unittest
from unittest.mock import patch

from app.ai_explainer import explain_prediction


class AIExplainerTests(unittest.TestCase):
    @patch("app.ai_explainer.urllib.request.urlopen")
    def test_ollama_response_is_returned(self, mock_urlopen):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"response":"- Risk is high."}'

        mock_urlopen.return_value = Response()
        result = explain_prediction({"product": "Protein", "urgency": "high"})
        self.assertEqual(result, "- Risk is high.")


if __name__ == "__main__":
    unittest.main()

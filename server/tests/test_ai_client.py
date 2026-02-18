"""AI 客户端重试与主备切换测试。"""
import unittest
from unittest.mock import MagicMock, patch

from ai.ai_client import AIClient, AIClientError


class TestAIClient(unittest.TestCase):
    @patch("ai.ai_client.time.sleep", return_value=None)
    def test_retry_success_on_primary(self, _):
        primary = MagicMock()
        primary.call.side_effect = [RuntimeError("x"), "ok"]

        with patch.object(AIClient, "_create_adapter", side_effect=[primary]):
            client = AIClient()
            result = client.generate("prompt", max_retries=2)

        self.assertEqual(result, "ok")
        self.assertEqual(primary.call.call_count, 2)

    @patch("ai.ai_client.time.sleep", return_value=None)
    def test_switch_to_fallback_when_primary_failed(self, _):
        primary = MagicMock()
        primary.call.side_effect = RuntimeError("primary fail")
        fallback = MagicMock()
        fallback.call.return_value = "fallback ok"

        with patch("ai.ai_client.Config.AI_FALLBACK_PROVIDER", "zhipu"), patch(
            "ai.ai_client.Config.AI_FALLBACK_API_KEY", "dummy"
        ), patch.object(AIClient, "_create_adapter", side_effect=[primary, fallback]):
            client = AIClient()
            result = client.generate("prompt", max_retries=1)

        self.assertEqual(result, "fallback ok")
        self.assertEqual(primary.call.call_count, 1)
        self.assertEqual(fallback.call.call_count, 1)


if __name__ == "__main__":
    unittest.main()

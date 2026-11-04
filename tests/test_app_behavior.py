import unittest
from unittest.mock import patch

import app as app_module


class AppBehaviorTests(unittest.TestCase):
    def test_send_message_returns_503_when_ai_service_fails(self) -> None:
        def fake_error(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=150):
            self.last_error = "network connection failed"
            return "temporary fallback"

        with patch.object(app_module.AIService, "get_chat_response", fake_error):
            app = app_module.create_app("development")
            client = app.test_client()
            response = client.post("/send_message", json={"message": "hello"})

        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"], "network connection failed")

    def test_health_reports_degraded_when_ai_service_fails(self) -> None:
        def fake_error(self, messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=150):
            self.last_error = "network connection failed"
            return "temporary fallback"

        with patch.object(app_module.AIService, "get_chat_response", fake_error):
            app = app_module.create_app("development")
            client = app.test_client()
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["services"]["ai_service"], "error")
        self.assertEqual(payload["details"]["ai_service"], "network connection failed")


if __name__ == "__main__":
    unittest.main()

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import app
from rag import Passage


class AppTests(unittest.TestCase):
    def test_validate_question(self):
        self.assertEqual(app.validate_question("  ERP login issue  "), "ERP login issue")
        with self.assertRaises(ValueError):
            app.validate_question("")
        with self.assertRaises(ValueError):
            app.validate_question(123)

    def test_health_route(self):
        event = {"requestContext": {"http": {"method": "GET"}}, "rawPath": "/health"}
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["status"], "ok")

    def test_support_rejects_missing_question(self):
        event = {
            "requestContext": {"http": {"method": "POST"}},
            "rawPath": "/support",
            "body": "{}",
        }
        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    def test_no_match_does_not_invoke_model(self):
        passages = [Passage("erp.md", "Work order", "Check the plant and routing records.")]
        with patch.object(app, "invoke_grounded_model") as model:
            result = app.answer_question("What is the weather?", passages)
        model.assert_not_called()
        self.assertFalse(result["grounded"])
        self.assertTrue(result["escalation_required"])
        self.assertEqual(result["citations"], [])

    def test_grounded_match_returns_citation(self):
        passages = [
            Passage(
                "erp.md",
                "Work order release troubleshooting",
                "Confirm plant context, work order status, material, routing, and exact ERP error.",
            )
        ]
        with patch.object(app, "invoke_grounded_model", return_value="Check the plant context and routing first."):
            result = app.answer_question("Why will my ERP work order not release due to routing?", passages)
        self.assertTrue(result["grounded"])
        self.assertEqual(result["citations"][0]["source"], "erp.md")


if __name__ == "__main__":
    unittest.main()

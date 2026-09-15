import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag import Passage, chunk_markdown, fallback_answer, requires_escalation, retrieve


class RagTests(unittest.TestCase):
    def test_chunk_markdown_tracks_sections(self):
        text = "# Title\nIntro text.\n\n## Work Order\nCheck status and routing."
        passages = chunk_markdown("sample.md", text)
        self.assertEqual(passages[0].section, "Title")
        self.assertEqual(passages[1].section, "Work Order")

    def test_retrieve_prefers_relevant_passage(self):
        passages = [
            Passage("erp.md", "Work order release troubleshooting", "Check plant, status, material, routing, and the exact ERP error."),
            Passage("pc.md", "Printer support", "Check the printer queue and paper tray."),
        ]
        matches = retrieve("ERP work order will not release because of routing", passages, top_k=2)
        self.assertTrue(matches)
        self.assertEqual(matches[0].source, "erp.md")
        self.assertGreater(matches[0].score, 0)

    def test_irrelevant_question_returns_no_match(self):
        passages = [Passage("erp.md", "Work order", "Check plant and routing records.")]
        self.assertEqual(retrieve("What is the weather tomorrow?", passages), [])

    def test_security_incident_requires_escalation(self):
        self.assertTrue(requires_escalation("We think this workstation has ransomware"))
        self.assertFalse(requires_escalation("How do I check a barcode transaction?"))

    def test_fallback_is_safe(self):
        answer = fallback_answer().lower()
        self.assertIn("could not find", answer)
        self.assertIn("do not improvise", answer)
        self.assertIn("escalate", answer)


if __name__ == "__main__":
    unittest.main()

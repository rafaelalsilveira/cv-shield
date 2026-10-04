import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api import MAX_FILE_SIZE, app

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

FAKE_ASSESSMENT = {
    "risk_level": "high",
    "reasoning": "motivo falso",
    "recommendation": "acao falsa",
}


def read_example(filename):
    """Le um PDF da pasta examples e devolve os bytes."""
    with open(os.path.join(EXAMPLES_DIR, filename), "rb") as pdf_file:
        return pdf_file.read()


def post_pdf(client, data, filename="resume.pdf"):
    """Envia bytes para o /analyze como upload, igual ao n8n faz."""
    return client.post(
        "/analyze",
        files={"file": (filename, data, "application/pdf")},
    )


class TestApi(unittest.TestCase):

    def setUp(self):
        # raise_server_exceptions=False faz erros internos virarem status 500
        # (como na API de verdade), em vez de estourar dentro do teste.
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_health_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("src.main.analyze_with_ai", return_value=FAKE_ASSESSMENT)
    def test_clean_resume_returns_report_without_findings(self, fake_ai):
        data = read_example("sample_resume.pdf")

        response = post_pdf(self.client, data, filename="sample_resume.pdf")

        self.assertEqual(response.status_code, 200)
        report = response.json()
        self.assertEqual(report["file"], "sample_resume.pdf")
        self.assertEqual(report["summary"]["finding_count"], 0)
        self.assertEqual(report["findings"], [])

    @patch("src.main.analyze_with_ai", return_value=FAKE_ASSESSMENT)
    def test_suspicious_resume_returns_hidden_text_findings(self, fake_ai):
        data = read_example("CV Ra.pdf")

        response = post_pdf(self.client, data, filename="CV Ra.pdf")

        self.assertEqual(response.status_code, 200)
        report = response.json()
        self.assertEqual(report["file"], "CV Ra.pdf")
        self.assertGreater(report["summary"]["finding_count"], 0)
        categories = {finding["category"] for finding in report["findings"]}
        self.assertIn("hidden_text", categories)
        self.assertEqual(report["ai_assessment"], FAKE_ASSESSMENT)
        fake_ai.assert_called_once()

    def test_rejects_file_that_is_not_a_pdf(self):
        response = post_pdf(self.client, b"isto nao e um pdf")

        self.assertEqual(response.status_code, 400)
        self.assertIn("not a valid PDF", response.json()["detail"])

    def test_rejects_file_larger_than_limit(self):
        too_big = b"%PDF" + b"0" * MAX_FILE_SIZE

        response = post_pdf(self.client, too_big)

        self.assertEqual(response.status_code, 413)

    def test_rejects_corrupted_pdf(self):
        # Comeca com %PDF (passa na primeira checagem) mas nao e legivel.
        response = post_pdf(self.client, b"%PDF-1.4 conteudo quebrado")

        self.assertEqual(response.status_code, 400)

    def test_request_without_file_returns_422(self):
        response = self.client.post("/analyze")

        self.assertEqual(response.status_code, 422)

    def test_temporary_file_is_deleted_after_analysis(self):
        seen_paths = []

        def fake_analyze_pdf(pdf_path):
            seen_paths.append(pdf_path)
            return {"file": "temp.pdf"}

        with patch("src.api.analyze_pdf", side_effect=fake_analyze_pdf):
            response = post_pdf(self.client, b"%PDF-1.4 qualquer coisa")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(seen_paths), 1)
        self.assertFalse(os.path.exists(seen_paths[0]))


if __name__ == "__main__":
    unittest.main()
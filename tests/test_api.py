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


def make_report(finding_count=0, risk_level="not_reviewed", reasoning=None):
    """Monta, a mao, um relatorio no formato que o /analyze devolve.

    Nao usa PDF nem rede: o /batch-report so recebe o JSON pronto.
    """
    findings = []
    if finding_count > 0:
        findings = [
            {
                "category": "instruction_override",
                "pattern": "ignore previous instructions",
            }
        ]
    assessment = {"risk_level": risk_level}
    if reasoning:
        assessment["reasoning"] = reasoning
    return {
        "summary": {"finding_count": finding_count},
        "findings": findings,
        "ai_assessment": assessment,
    }


class TestBatchReportEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def post_batch(self, payload):
        return self.client.post("/batch-report", json=payload)

    def test_mixed_batch_returns_summary_and_unread_pile(self):
        payload = {
            "items": [
                {"file": "limpo.pdf", "report": make_report(0, "none")},
                {"file": "suspeito.pdf", "report": make_report(1, "high")},
                {
                    "file": "ia_falhou.pdf",
                    "report": make_report(0, "unknown", "AI request failed"),
                },
                {"file": "quebrado.pdf", "error": "Could not read the PDF."},
            ]
        }

        response = self.post_batch(payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            body["summary"],
            {"total": 4, "ok": 1, "attention": 1, "not_analyzed": 1, "error": 1},
        )
        self.assertIn("<h2>Não analisados</h2>", body["html"])
        self.assertIn("4 recebidos, 1 sinalizados, 2 não analisados", body["html"])

    def test_not_reviewed_without_findings_stays_ok(self):
        payload = {
            "items": [{"file": "a.pdf", "report": make_report(0, "not_reviewed")}]
        }

        body = self.post_batch(payload).json()

        self.assertEqual(body["summary"]["ok"], 1)
        self.assertEqual(body["summary"]["attention"], 0)
        self.assertEqual(body["summary"]["not_analyzed"], 0)

    def test_local_findings_with_ai_unknown_stay_attention(self):
        payload = {"items": [{"file": "a.pdf", "report": make_report(1, "unknown")}]}

        body = self.post_batch(payload).json()

        self.assertEqual(body["summary"]["attention"], 1)
        self.assertEqual(body["summary"]["not_analyzed"], 0)

    def test_empty_list_returns_page_without_pdfs(self):
        response = self.post_batch({"items": []})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["summary"]["total"], 0)
        self.assertIn("Nenhum PDF encontrado na pasta", body["html"])

    def test_item_with_report_and_error_returns_422(self):
        payload = {
            "items": [
                {"file": "a.pdf", "report": make_report(), "error": "texto"}
            ]
        }

        response = self.post_batch(payload)

        self.assertEqual(response.status_code, 422)
        self.assertIn("exactly one", response.text)

    def test_item_without_report_and_error_returns_422(self):
        response = self.post_batch({"items": [{"file": "a.pdf"}]})

        self.assertEqual(response.status_code, 422)
        self.assertIn("exactly one", response.text)

    def test_report_without_summary_returns_422_naming_the_file(self):
        payload = {"items": [{"file": "sem_resumo.pdf", "report": {"findings": []}}]}

        response = self.post_batch(payload)

        self.assertEqual(response.status_code, 422)
        self.assertIn("sem_resumo.pdf", response.json()["detail"])

    def test_default_and_custom_folder_appear_on_the_page(self):
        items = [{"file": "a.pdf", "report": make_report()}]

        default_page = self.post_batch({"items": items}).json()["html"]
        custom_page = self.post_batch(
            {"items": items, "folder": "Triagem de outubro"}
        ).json()["html"]

        self.assertIn("Enviados pelo n8n", default_page)
        self.assertIn("Triagem de outubro", custom_page)
        self.assertNotIn("Enviados pelo n8n", custom_page)

    def test_file_name_with_script_tag_is_escaped(self):
        name = "<script>alert(1)</script>.pdf"
        payload = {"items": [{"file": name, "report": make_report()}]}

        page = self.post_batch(payload).json()["html"]

        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_status_sent_by_the_client_is_ignored(self):
        # O cliente diz "attention", mas o relatorio esta limpo: quem decide
        # o status e o classify_report, entao o resultado tem que ser "ok".
        payload = {
            "items": [
                {
                    "file": "a.pdf",
                    "status": "attention",
                    "report": make_report(0, "none"),
                }
            ]
        }

        body = self.post_batch(payload).json()

        self.assertEqual(body["summary"]["ok"], 1)
        self.assertEqual(body["summary"]["attention"], 0)

    def test_request_without_items_returns_422(self):
        response = self.post_batch({"folder": "qualquer"})

        self.assertEqual(response.status_code, 422)

    def test_report_without_findings_returns_422_naming_the_file(self):
        payload = {
            "items": [
                {
                    "file": "sem_achados.pdf",
                    "report": {"summary": {"finding_count": 0}},
                }
            ]
        }

        response = self.post_batch(payload)

        self.assertEqual(response.status_code, 422)
        self.assertIn("sem_achados.pdf", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

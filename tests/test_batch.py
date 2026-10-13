import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.batch import analyze_folder, classify_report, list_pdfs

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

CLEAN_ASSESSMENT = {
    "risk_level": "not_reviewed",
    "reasoning": "motivo falso",
    "recommendation": "acao falsa",
}
HIGH_ASSESSMENT = {
    "risk_level": "high",
    "reasoning": "motivo falso",
    "recommendation": "acao falsa",
}


def make_report(finding_count=0, risk_level="not_reviewed"):
    """Monta um relatório no mesmo formato do analyze_pdf."""
    return {
        "file": "x.pdf",
        "status": "completed",
        "summary": {"finding_count": finding_count},
        "findings": [{"category": "hidden_text"}] * finding_count,
        "ai_assessment": {"risk_level": risk_level},
    }


class TestClassifyReport(unittest.TestCase):

    def test_no_findings_and_not_reviewed_is_ok(self):
        self.assertEqual(classify_report(make_report(0, "not_reviewed")), "ok")

    def test_no_findings_and_none_is_ok(self):
        self.assertEqual(classify_report(make_report(0, "none")), "ok")

    def test_ai_failure_without_findings_is_ok(self):
        self.assertEqual(classify_report(make_report(0, "unknown")), "ok")

    def test_findings_mean_attention(self):
        self.assertEqual(classify_report(make_report(2, "high")), "attention")

    def test_findings_mean_attention_even_if_ai_says_none(self):
        self.assertEqual(classify_report(make_report(1, "none")), "attention")

    def test_ai_medium_without_findings_means_attention(self):
        # Ataque visível e parafraseado, pego só pela IA (AI_REVIEW_MODE=always).
        self.assertEqual(classify_report(make_report(0, "medium")), "attention")


class TestListPdfs(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)

    def touch(self, name):
        Path(self.folder, name).write_bytes(b"x")

    def test_lists_only_pdfs_in_name_order(self):
        self.touch("b.pdf")
        self.touch("A.PDF")
        self.touch("notas.txt")
        self.touch("c.docx")

        names = [path.name for path in list_pdfs(self.folder)]

        self.assertEqual(names, ["A.PDF", "b.pdf"])

    def test_ignores_subfolders(self):
        os.mkdir(os.path.join(self.folder, "velhos.pdf"))
        self.touch("a.pdf")

        names = [path.name for path in list_pdfs(self.folder)]

        self.assertEqual(names, ["a.pdf"])

    def test_missing_folder_raises_clear_error(self):
        with self.assertRaises(FileNotFoundError):
            list_pdfs(os.path.join(self.folder, "nao_existe"))


class TestAnalyzeFolder(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)

    def copy_example(self, filename):
        shutil.copy(os.path.join(EXAMPLES_DIR, filename), self.folder)

    def test_empty_folder_returns_zero_summary(self):
        batch = analyze_folder(self.folder)

        self.assertEqual(
            batch["summary"], {"total": 0, "ok": 0, "attention": 0, "error": 0}
        )
        self.assertEqual(batch["results"], [])

    @patch("src.main.analyze_with_ai", return_value=CLEAN_ASSESSMENT)
    def test_clean_and_suspicious_resumes_are_separated(self, fake_ai):
        self.copy_example("sample_resume.pdf")
        self.copy_example("CV Ra.pdf")

        batch = analyze_folder(self.folder)

        status_by_file = {r["file"]: r["status"] for r in batch["results"]}
        self.assertEqual(status_by_file["sample_resume.pdf"], "ok")
        self.assertEqual(status_by_file["CV Ra.pdf"], "attention")
        self.assertEqual(
            batch["summary"], {"total": 2, "ok": 1, "attention": 1, "error": 0}
        )

    @patch("src.main.analyze_with_ai", return_value=HIGH_ASSESSMENT)
    def test_flagged_row_keeps_the_full_report(self, fake_ai):
        self.copy_example("CV Ra.pdf")

        row = analyze_folder(self.folder)["results"][0]

        self.assertGreater(row["finding_count"], 0)
        self.assertEqual(row["risk_level"], "high")
        self.assertEqual(row["report"]["ai_assessment"], HIGH_ASSESSMENT)
        categories = {f["category"] for f in row["report"]["findings"]}
        self.assertIn("hidden_text", categories)

    @patch("src.main.analyze_with_ai", return_value=CLEAN_ASSESSMENT)
    def test_broken_pdf_becomes_error_and_does_not_stop_the_others(self, fake_ai):
        # "a_" vem antes e "z_" depois do PDF quebrado na ordem de nome.
        shutil.copy(
            os.path.join(EXAMPLES_DIR, "sample_resume.pdf"),
            os.path.join(self.folder, "a_good.pdf"),
        )
        Path(self.folder, "b_broken.pdf").write_bytes(b"%PDF-1.4 conteudo quebrado")
        shutil.copy(
            os.path.join(EXAMPLES_DIR, "sample_resume.pdf"),
            os.path.join(self.folder, "z_good.pdf"),
        )

        batch = analyze_folder(self.folder)

        status_by_file = {r["file"]: r["status"] for r in batch["results"]}
        self.assertEqual(
            status_by_file,
            {"a_good.pdf": "ok", "b_broken.pdf": "error", "z_good.pdf": "ok"},
        )
        broken = batch["results"][1]
        self.assertIn("error", broken)
        self.assertNotIn("report", broken)
        self.assertEqual(
            batch["summary"], {"total": 3, "ok": 2, "attention": 0, "error": 1}
        )

    def test_any_exception_from_analyze_pdf_becomes_error(self):
        Path(self.folder, "um.pdf").write_bytes(b"x")
        Path(self.folder, "dois.pdf").write_bytes(b"x")

        with patch("src.batch.analyze_pdf", side_effect=RuntimeError("boom")):
            batch = analyze_folder(self.folder)

        self.assertEqual(batch["summary"]["error"], 2)
        self.assertEqual(batch["results"][0]["error"], "RuntimeError: boom")


if __name__ == "__main__":
    unittest.main()

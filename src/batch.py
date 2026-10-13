"""Analisa todos os PDFs de uma pasta (lote de currículos).

Reaproveita o analyze_pdf (src/main.py). Um PDF quebrado vira status "error"
e não derruba os outros. Quem decide o que fazer com os sinalizados é uma
pessoa: aqui só se separa o que está ok do que merece atenção.
"""
from pathlib import Path

from src.main import analyze_pdf

# Níveis de risco da IA que mandam o currículo para "attention", mesmo sem
# achados dos detectores locais (acontece com AI_REVIEW_MODE=always, quando a
# IA lê um ataque visível e parafraseado). "none", "not_reviewed" e "unknown"
# não sinalizam: "unknown" é a IA que falhou, e sem achados locais não há
# evidência para apontar o currículo.
ATTENTION_RISK_LEVELS = ("low", "medium", "high")


def list_pdfs(folder):
    """Devolve os PDFs da pasta (não entra em subpastas), em ordem de nome.

    Não usa glob("*.pdf") porque no Linux ele não acha "CV.PDF" e no Windows
    acha: comparar a extensão em minúsculas dá o mesmo resultado nos dois.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder}")

    pdfs = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    ]
    return sorted(pdfs, key=lambda path: path.name.lower())


def classify_report(report):
    """Decide o status de um relatório: "attention" ou "ok"."""
    if report["summary"]["finding_count"] > 0:
        return "attention"

    ai_assessment = report.get("ai_assessment") or {}
    if ai_assessment.get("risk_level") in ATTENTION_RISK_LEVELS:
        return "attention"

    return "ok"


def analyze_one(pdf_path):
    """Analisa um PDF e devolve uma linha do lote. Nunca levanta erro."""
    try:
        report = analyze_pdf(str(pdf_path))
    except Exception as exc:
        return {
            "file": pdf_path.name,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }

    ai_assessment = report.get("ai_assessment") or {}
    return {
        "file": pdf_path.name,
        "status": classify_report(report),
        "finding_count": report["summary"]["finding_count"],
        "risk_level": ai_assessment.get("risk_level"),
        "report": report,
    }


def analyze_folder(folder):
    """Analisa todos os PDFs da pasta e devolve resumo + uma linha por PDF."""
    results = [analyze_one(pdf_path) for pdf_path in list_pdfs(folder)]

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "attention": sum(1 for r in results if r["status"] == "attention"),
        "error": sum(1 for r in results if r["status"] == "error"),
    }

    return {"folder": str(folder), "summary": summary, "results": results}

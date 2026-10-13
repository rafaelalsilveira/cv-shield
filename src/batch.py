"""Analisa todos os PDFs de uma pasta (lote de currículos).

Reaproveita o analyze_pdf (src/main.py). Um PDF quebrado vira status "error"
e não derruba os outros. Quem decide o que fazer com os sinalizados é uma
pessoa: aqui só se separa o que está ok do que merece atenção.

Uso: python -m src.batch minha_pasta
"""
import argparse
import sys
from pathlib import Path

from src.ai_analysis import get_review_mode
from src.batch_report import save_html
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


def analyze_folder(folder, on_result=None):
    """Analisa todos os PDFs da pasta e devolve resumo + uma linha por PDF.

    on_result (opcional) é chamada a cada PDF terminado, como
    on_result(posição, total, linha), para quem quiser mostrar o andamento.
    """
    pdfs = list_pdfs(folder)
    results = []

    for position, pdf_path in enumerate(pdfs, start=1):
        row = analyze_one(pdf_path)
        results.append(row)
        if on_result is not None:
            on_result(position, len(pdfs), row)

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "attention": sum(1 for r in results if r["status"] == "attention"),
        "error": sum(1 for r in results if r["status"] == "error"),
    }

    return {"folder": str(folder), "summary": summary, "results": results}


DEFAULT_OUTPUT = "relatorio_lote.html"

PROGRESS_LABELS = {"ok": "ok", "attention": "ATENÇÃO", "error": "ERRO"}


def print_progress(position, total, row):
    """Uma linha por currículo terminado, para o terminal não parecer travado."""
    label = PROGRESS_LABELS[row["status"]]
    print(f"[{position}/{total}] {row['file']} ... {label}", flush=True)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="python -m src.batch",
        description="Analisa todos os PDFs de uma pasta e gera um relatório HTML.",
    )
    parser.add_argument("folder", help="pasta com os currículos em PDF")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"arquivo HTML do relatório (padrão: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args(argv)


def describe_review_mode(mode):
    if mode == "always":
        return "always (a IA lê o texto de TODOS os currículos)"
    return "findings_only (a IA só lê os currículos em que os detectores acharam algo)"


def main(argv=None):
    """Roda o lote pela linha de comando. Devolve 0 se deu certo, 1 se não deu."""
    # Terminais do Windows nem sempre usam UTF-8; sem isso, acentos quebram.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args(argv)

    try:
        pdfs = list_pdfs(args.folder)
    except FileNotFoundError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if not pdfs:
        print(f"Nenhum PDF encontrado em {args.folder}. Nada a analisar.")
        return 0

    print(f"Analisando {len(pdfs)} PDF(s) de {args.folder}")
    print(f"Modo da IA: {describe_review_mode(get_review_mode())}\n")

    batch = analyze_folder(args.folder, on_result=print_progress)
    save_html(batch, args.output)

    summary = batch["summary"]
    print(f"\n{summary['total']} analisados, {summary['attention']} sinalizados", end="")
    print(f", {summary['error']} com erro" if summary["error"] else "")

    for row in batch["results"]:
        if row["status"] == "attention":
            print(f"  ATENÇÃO  {row['file']}")
        elif row["status"] == "error":
            print(f"  ERRO     {row['file']}: {row['error']}")

    print(f"\nRelatório salvo em: {args.output}")
    print("Esta ferramenta só aponta sinais: a decisão sobre cada currículo é humana.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

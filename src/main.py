import json

from dotenv import load_dotenv
from pypdf import PdfReader
from os.path import basename
from src.detector import detect_suspicious_patterns
from src.hidden_text import extract_text_fragments, find_hidden_text
from src.ai_analysis import analyze_with_ai

load_dotenv()


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


def create_report(pdf_path, findings, ai_assessment=None):
    return {
        "file": basename(pdf_path),
        "status": "completed",
        "summary": {
            "finding_count": len(findings),
        },
        "findings": findings,
        "ai_assessment": ai_assessment,
    }


def analyze_pdf(pdf_path):
    """Run the full analysis pipeline on a PDF and return the report (dict)."""
    extracted_text = extract_text_from_pdf(pdf_path)
    text_findings = detect_suspicious_patterns(extracted_text)

    fragments = extract_text_fragments(pdf_path)
    hidden_findings = find_hidden_text(fragments)

    all_findings = text_findings + hidden_findings
    ai_assessment = analyze_with_ai(extracted_text, all_findings)

    return create_report(pdf_path, all_findings, ai_assessment)


def main():
    pdf_path = "examples/sample_resume.pdf"
    report = analyze_pdf(pdf_path)
    extracted_text = extract_text_from_pdf(pdf_path)

    print("Structured report:")
    print(json.dumps(report, indent=4, ensure_ascii=False))

    print("Texto extraído do currículo:")
    print(extracted_text)

    print("\nPadrões suspeitos encontrados:")

    if report["findings"]:
        for finding in report["findings"]:
            category = finding["category"]
            pattern = finding["pattern"]

            print(f"- Categoria: {category}")
            print(f"  Padrão: {pattern}")

            if category == "hidden_text":
                print(f"  Página: {finding['page']}")
                print(f"  Trechos agrupados: {finding['fragment_count']}")
                print(f"  Prévia: {finding['text_preview']}")

    else:
        print("Nenhum padrão suspeito encontrado.")

    print("\nParecer da IA:")
    print(f"  Nível de risco: {report['ai_assessment']['risk_level']}")
    print(f"  Justificativa: {report['ai_assessment']['reasoning']}")
    print(f"  Recomendação: {report['ai_assessment']['recommendation']}")


if __name__ == "__main__":
    main()
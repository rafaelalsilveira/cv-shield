import json

from pypdf import PdfReader
from os.path import basename
from src.detector import detect_suspicious_patterns
from src.hidden_text import extract_text_fragments, find_hidden_text


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


def create_report(pdf_path, findings):
    return {
        "file": basename(pdf_path),
        "status": "completed",
        "summary": {
            "finding_count": len(findings),
        },
        "findings": findings,
    }


def main():
    pdf_path = "examples/sample_resume.pdf"
    extracted_text = extract_text_from_pdf(pdf_path)
    text_findings = detect_suspicious_patterns(extracted_text)

    fragments = extract_text_fragments(pdf_path)
    hidden_findings = find_hidden_text(fragments)

    all_findings = text_findings + hidden_findings
    report = create_report(pdf_path, all_findings)

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


if __name__ == "__main__":
    main()
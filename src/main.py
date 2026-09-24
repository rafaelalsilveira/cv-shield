from pypdf import PdfReader
from os.path import basename
from src.detector import detect_suspicious_patterns


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

    findings = detect_suspicious_patterns(extracted_text)
    report = create_report(pdf_path, findings)

    print("Texto extraído do currículo:")
    print(extracted_text)

    print("\nPadrões suspeitos encontrados:")

    if report["findings"]:
        for finding in report["findings"]:
            category = finding["category"]
            pattern = finding["pattern"]

            print(f"- Categoria: {category}")
            print(f"  Padrão: {pattern}")

    else:
        print("Nenhum padrão suspeito encontrado.")


if __name__ == "__main__":
    main()

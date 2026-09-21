from pypdf import PdfReader
from detector import detect_suspicious_patterns


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


def main():
    pdf_path = "examples/sample_resume.pdf"

    extracted_text = extract_text_from_pdf(pdf_path)

    findings = detect_suspicious_patterns(extracted_text)

    print("Texto extraído do currículo:")
    print(extracted_text)

    print("\nPadrões suspeitos encontrados:")

    if findings:
        for finding in findings:
            print(f"- {finding}")
    else:
        print("Nenhum padrão suspeito encontrado.")


if __name__ == "__main__":
    main()
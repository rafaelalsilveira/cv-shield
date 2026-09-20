
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


def main():
    pdf_path = "examples/sample_resume.pdf"

    extracted_text = extract_text_from_pdf(pdf_path)

    print("Texto extraído do currículo:")
    print(extracted_text)


if __name__ == "__main__":
    main()
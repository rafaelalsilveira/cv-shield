"""Run only the local detectors on every PDF in a folder. Does NOT call Groq.

Prints a table and saves a CSV with one row per finding.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.main import extract_text_from_pdf
from src.detector import detect_suspicious_patterns
from src.hidden_text import extract_text_fragments, find_hidden_text

sys.stdout.reconfigure(encoding="utf-8")

CSV_FIELDS = ["file", "finding_count", "category", "pattern", "page", "text_preview"]


def analyze_local(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    text_findings = detect_suspicious_patterns(text)
    hidden_findings = find_hidden_text(extract_text_fragments(pdf_path))
    return text_findings + hidden_findings


def validate_folder(folder, csv_path):
    pdfs = sorted(Path(folder).glob("*.pdf"))
    rows = []

    print(f"{'file':32} {'n':>3}  {'category':14} patterns")
    print("-" * 90)

    for pdf in pdfs:
        try:
            findings = analyze_local(str(pdf))
        except Exception as exc:
            print(f"{pdf.name:32} ERROR: {exc}")
            rows.append({"file": pdf.name, "finding_count": "ERROR", "pattern": str(exc)})
            continue

        if not findings:
            print(f"{pdf.name:32} {0:>3}")
            rows.append({"file": pdf.name, "finding_count": 0})
            continue

        for i, f in enumerate(findings):
            name = pdf.name if i == 0 else ""
            count = len(findings) if i == 0 else ""
            print(f"{name:32} {count:>3}  {f['category']:14} {f['pattern']}")
            rows.append({
                "file": pdf.name,
                "finding_count": len(findings),
                "category": f["category"],
                "pattern": f["pattern"],
                "page": f.get("page", ""),
                "text_preview": f.get("text_preview", ""),
            })

    # utf-8-sig and ";" so Excel in pt-BR opens it correctly
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV saved to {csv_path}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "examples"
    out = sys.argv[2] if len(sys.argv) > 2 else "experiments/validation_results.csv"
    validate_folder(folder, out)
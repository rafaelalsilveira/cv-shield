import os
import tempfile
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, model_validator
from pypdf.errors import PdfReadError

from src.batch import build_error_row, build_row, build_summary
from src.batch_report import render_html
from src.main import analyze_pdf

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Name shown on the page when n8n does not say which folder the batch came from.
DEFAULT_BATCH_FOLDER = "Enviados pelo n8n"

app = FastAPI(
    title="CV Shield API",
    description="Analyzes PDF resumes for hidden text and suspicious instructions.",
)


@app.get("/health")
def health():
    """Simple check so n8n (or you) can see that the API is running."""
    return {"status": "ok"}


@app.post("/analyze")
def analyze(file: UploadFile = File(...)):
    """Receive a PDF upload, run the CV Shield pipeline and return the report."""
    data = file.file.read(MAX_FILE_SIZE + 1)

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB).")

    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF.")

    # analyze_pdf expects a file path, so we write the upload to a temp file.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(data)
        temp_path = temp_file.name

    try:
        report = analyze_pdf(temp_path)
    except PdfReadError:
        raise HTTPException(status_code=400, detail="Could not read the PDF.")
    finally:
        os.remove(temp_path)

    # The report would show the temp file name, so we put the original name back.
    report["file"] = file.filename
    return report


class BatchItem(BaseModel):
    """One resume in the batch: either its /analyze report or the error n8n got.

    Extra fields (like a "status" sent by the client) are ignored on purpose:
    the status is always decided by classify_report in src/batch.py.
    """

    file: str
    report: Optional[dict] = None
    error: Optional[str] = None

    @model_validator(mode="after")
    def check_exactly_one_of_report_or_error(self):
        if (self.report is None) == (self.error is None):
            raise ValueError("Each item needs exactly one of 'report' or 'error'.")
        return self


class BatchReportRequest(BaseModel):
    items: list[BatchItem]
    folder: Optional[str] = None


def check_report_shape(item):
    """Make sure a report has what the page needs, naming the file if not."""
    report = item.report
    summary = report.get("summary")
    has_count = isinstance(summary, dict) and "finding_count" in summary
    has_findings = isinstance(report.get("findings"), list)

    if not (has_count and has_findings):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Report for '{item.file}' needs summary.finding_count "
                "and findings."
            ),
        )


@app.post("/batch-report")
def batch_report(request: BatchReportRequest):
    """Receive the results of many /analyze calls and return the HTML page.

    n8n coordinates (one call per PDF); the rules for the piles live here.
    """
    for item in request.items:
        if item.report is not None:
            check_report_shape(item)

    try:
        results = []
        for item in request.items:
            if item.error is not None:
                results.append(build_error_row(item.file, item.error))
            else:
                results.append(build_row(item.file, item.report))

        batch = {
            "folder": request.folder or DEFAULT_BATCH_FOLDER,
            "summary": build_summary(results),
            "results": results,
        }
        html_page = render_html(batch)
    except Exception:
        # A report with a strange format must never become a 500 for n8n.
        raise HTTPException(
            status_code=422,
            detail="Could not build the page from the reports sent.",
        )

    return {"summary": batch["summary"], "html": html_page}

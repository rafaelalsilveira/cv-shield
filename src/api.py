import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from pypdf.errors import PdfReadError

from src.main import analyze_pdf

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

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
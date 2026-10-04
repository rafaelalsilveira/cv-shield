# n8n integration

The `n8n/` folder contains an exported workflow (`cv-shield-analyze-resume.json`) that sends a resume to the CV Shield API and shows the report.

## Workflow

1. **Receber currículo (formulário)**: an n8n Form Trigger that creates a web page with a PDF upload field.
2. **Analisar com CV Shield**: an HTTP Request node that sends the uploaded PDF to `POST http://127.0.0.1:8000/analyze` and receives the report.

## How to use it

1. Start the API (see the Quick start in the main README) and n8n.
2. In n8n, open the workflow menu, choose **Import from file...** and select `n8n/cv-shield-analyze-resume.json`.
3. Click **Execute workflow**, upload a PDF in the form that opens, and check the output of the HTTP Request node.

## Details worth knowing

- n8n names the binary field after the form field label, replacing characters it does not accept. The label `Currículo` becomes `Curr_culo`, which is the value the HTTP Request node expects in **Input Data Field Name**. If you rename the form field, update that value as well.
- n8n restricts which folders its file nodes can read, so reading a PDF from an arbitrary project folder fails with "Access to the file is not allowed". Using an upload form avoids this.
- The exported JSON does not contain credentials or API keys. The Groq key lives only in the API's `.env` file; n8n never sees it.
---
name: markerpdf-cli
description: Convert a PDF to Markdown using the MarkerPDF service. Use this skill whenever the user wants to parse, convert, or extract text/images from a PDF, or mentions "markerpdf", "marker", "PDF to markdown", or "PDF parsing". Also trigger when the user provides a PDF file path and asks to process it.
---

# MarkerPDF CLI Skill

Convert a PDF to Markdown + images via the remote MarkerPDF server.

## When to use

User provides a PDF path (or asks to process one) and wants the result as Markdown with images extracted alongside the original PDF.

## How it works

1. Upload the PDF to the MarkerPDF server via the v2 API
2. Poll for job completion (up to 2 minutes)
3. Download the ZIP result and extract alongside the PDF (flat, no subdirectory)

## Configuration

Read credentials from the `.env` file in the project root (`/home/DataTransfer/Pyrojewel/01_lab/markerpdf_zotero/.env`). The file must contain:

```
MARKERPDF_SERVER_URL=http://localhost:11014
MARKERPDF_API_KEY=your-api-key-here
```

If the `.env` file is missing or incomplete, tell the user to create it and stop.

## Execution

Run the bundled script `scripts/markerpdf_convert.py` with the PDF path as argument:

```bash
python3 <skill-dir>/scripts/markerpdf_convert.py /path/to/document.pdf
```

The script:
- Reads `.env` for `MARKERPDF_SERVER_URL` and `MARKERPDF_API_KEY`
- Uploads the PDF with `POST /api/v2/submit`
- Polls `GET /api/v2/status/{job_id}` every 10 seconds, up to 2 minutes
- Downloads the ZIP from `GET /api/v2/download/{job_id}`
- Extracts to `<pdf_dir>/` with `<pdf_stem>.md` and images (flat alongside PDF)

## Output

On success, the script prints the result directory path:
```
OK: /path/to/pdf_dir/
```

On failure, it prints:
```
ERROR: <reason>
```

Report the result to the user. If successful, tell them the output location and that `content.md` is the main Markdown file. If it failed, share the error message.

## Example usage

User says: "parse /home/user/papers/article.pdf"
→ Run: `python3 <skill-dir>/scripts/markerpdf_convert.py /home/user/papers/article.pdf`
→ Tell user: "Done. Markdown at /home/user/papers/article.md"

User says: "convert this PDF to markdown" with a file path in context
→ Same flow.

## Important

- Always use absolute paths for the PDF input
- The script handles all API communication — do not call the API manually
- Timeout is 2 minutes; large PDFs may need longer — warn the user if it times out
- The `.env` file must exist before running; do not hardcode credentials

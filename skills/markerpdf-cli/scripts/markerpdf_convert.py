#!/usr/bin/env python3
"""Convert a PDF to Markdown via the MarkerPDF v2 API.

Usage: python3 markerpdf_convert.py /path/to/document.pdf

Reads MARKERPDF_SERVER_URL and MARKERPDF_API_KEY from .env in the
project root, then uploads, polls, downloads and extracts.
"""

import io
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

import httpx

# Resolve .env: walk up from CWD first, then from PDF directory
def _find_env(start: Path) -> Path | None:
    d = start
    for _ in range(5):
        candidate = d / ".env"
        if candidate.is_file():
            return candidate
        if d.parent == d:
            break
        d = d.parent
    return None


def load_env(pdf_path: Path) -> dict:
    dotenv = _find_env(Path.cwd()) or _find_env(pdf_path.parent)
    env = {}
    if dotenv:
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main():
    if len(sys.argv) < 2:
        print("ERROR: usage: markerpdf_convert.py <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1]).resolve()
    if not pdf_path.is_file():
        print(f"ERROR: file not found: {pdf_path}")
        sys.exit(1)
    if not pdf_path.suffix.lower() == ".pdf":
        print(f"ERROR: not a PDF: {pdf_path}")
        sys.exit(1)

    env = load_env(pdf_path)
    server_url = env.get("MARKERPDF_SERVER_URL", os.getenv("MARKERPDF_SERVER_URL", "")).rstrip("/")
    api_key = env.get("MARKERPDF_API_KEY", os.getenv("MARKERPDF_API_KEY", ""))

    if not server_url:
        print("ERROR: MARKERPDF_SERVER_URL not set in .env or environment")
        sys.exit(1)

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    stem = pdf_path.stem
    timeout = 120  # 2 minutes

    # Submit
    print(f"Submitting {pdf_path.name}...", file=sys.stderr)
    try:
        with open(pdf_path, "rb") as f:
            resp = httpx.post(
                f"{server_url}/api/v2/submit",
                headers=headers,
                files={"file": (pdf_path.name, f, "application/pdf")},
                data={"manifest": json.dumps({"source": "cli", "pdf_stem": stem})},
                timeout=60.0,
            )
    except httpx.RequestError as e:
        print(f"ERROR: connection failed: {e}")
        sys.exit(1)

    if resp.status_code == 401:
        print("ERROR: authentication failed (401) — check MARKERPDF_API_KEY")
        sys.exit(1)
    if resp.status_code != 202:
        print(f"ERROR: submit returned HTTP {resp.status_code}: {resp.text[:200]}")
        sys.exit(1)

    job_id = resp.json()["job_id"]
    print(f"Job ID: {job_id}", file=sys.stderr)

    # Poll
    print("Waiting for conversion...", file=sys.stderr)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sr = httpx.get(
                f"{server_url}/api/v2/status/{job_id}",
                headers=headers,
                timeout=30.0,
            )
        except httpx.RequestError as e:
            print(f"ERROR: status poll failed: {e}", file=sys.stderr)
            time.sleep(5)
            continue

        if sr.status_code != 200:
            print(f"ERROR: status returned HTTP {sr.status_code}")
            sys.exit(1)

        st = sr.json()
        if st.get("status") == "success":
            break
        if st.get("status") == "error":
            err = st.get("result", {}).get("error", "unknown error")
            print(f"ERROR: conversion failed: {err}")
            sys.exit(1)

        pct = st.get("percent", 0)
        print(f"  {st.get('status', '?')} {pct}% — {st.get('phase', '')}", file=sys.stderr)
        time.sleep(10)

    else:
        print(f"ERROR: timed out after {timeout}s")
        sys.exit(1)

    # Download
    print("Downloading result...", file=sys.stderr)
    try:
        dr = httpx.get(
            f"{server_url}/api/v2/download/{job_id}",
            headers=headers,
            timeout=120.0,
        )
    except httpx.RequestError as e:
        print(f"ERROR: download failed: {e}")
        sys.exit(1)

    if dr.status_code != 200:
        print(f"ERROR: download returned HTTP {dr.status_code}")
        sys.exit(1)

    # Extract to paper.marker/
    output_dir = pdf_path.parent / "paper.marker"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    with zipfile.ZipFile(io.BytesIO(dr.content)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            parts = Path(info.filename).parts
            # Strip top-level directory from ZIP entry
            filename = parts[-1] if len(parts) >= 2 else parts[0]
            # Rename .md to content.md
            if filename.endswith(".md"):
                filename = "content.md"
            with zf.open(info) as src, open(output_dir / filename, "wb") as dst:
                shutil.copyfileobj(src, dst)

    print(f"OK: {output_dir}")


if __name__ == "__main__":
    main()
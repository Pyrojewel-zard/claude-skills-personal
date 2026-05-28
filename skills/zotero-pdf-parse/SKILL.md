---
name: zotero-pdf-parse
description: "Parse a Zotero paper's PDF to Markdown via MarkerPDF. Trigger: user mentions Zotero item key and wants PDF-to-Markdown conversion, or says 'parse this Zotero paper'. Flow: item key → zotero-mcp get PDF path → markerpdf-cli convert."
argument-hint: "[Zotero item key]"
user_invocable: true
version: "1.0.0"
---

# Zotero PDF Parse

Given a Zotero item key, find the PDF attachment and convert it to Markdown via MarkerPDF.

## When to use

User provides a Zotero item key (8-char alphanumeric like `6X78HGMI`) and wants the PDF parsed to Markdown. Also trigger when user says "parse this Zotero paper" with an item key in context.

## How it works

1. Call `mcp__zotero-mcp__get_item_details` with the item key to get attachments
2. Pick the best PDF attachment (prefer `linkMode: 1` imported file over `linkMode: 0` linked file)
3. Convert the attachment `path` from Windows format to WSL absolute path:
   - `C:\Users\28956\Zotero\storage\KEY\file.pdf` → `/mnt/c/Users/28956/Zotero/storage/KEY/file.pdf`
4. Run markerpdf-cli conversion on that path
5. Report the result — `<pdf_stem>.md` will be alongside the PDF in the Zotero storage directory

## Execution

### Step 1: Get PDF path

```
mcp__zotero-mcp__get_item_details(itemKey="<ITEM_KEY>", mode="standard")
```

From the response, extract `attachments` array. Find PDF attachments where `contentType` is `application/pdf`. Prefer `linkMode: 1` (imported/stored file).

If no PDF attachment found, tell the user and stop.

### Step 2: Convert Windows path to WSL path

The `path` field from zotero-mcp uses Windows format. Transform it:
- Replace `C:\` with `/mnt/c/`
- Replace all `\` with `/`

Example: `C:\Users\28956\Zotero\storage\BUHQFDHA\2025_Jiang et al_Paper.pdf`
→ `/mnt/c/Users/28956/Zotero/storage/BUHQFDHA/2025_Jiang et al_Paper.pdf`

### Step 3: Run MarkerPDF conversion

```bash
python3 /home/holmes/.cc-switch/skills/markerpdf-cli/scripts/markerpdf_convert.py <WSL_PDF_PATH>
```

The script outputs `OK: <directory>` or `ERROR: <reason>`.

### Step 4: Report result

If successful: tell the user the `<pdf_stem>.md` location (same directory as the PDF, inside Zotero storage).

If failed: share the error message.

## Example usage

User says: "/zotero-pdf-parse CF2UFCPR"
→ Call `get_item_details(itemKey="CF2UFCPR")`
→ Find attachment `N2PYCG5D` with path `C:\Users\28956\Zotero\storage\N2PYCG5D\2010_Zhurbenko et al_Modeling of spiral inductors.pdf`
→ Convert to `/mnt/c/Users/28956/Zotero/storage/N2PYCG5D/2010_Zhurbenko et al_Modeling of spiral inductors.pdf`
→ Run: `python3 /home/holmes/.cc-switch/skills/markerpdf-cli/scripts/markerpdf_convert.py /mnt/c/Users/28956/Zotero/storage/N2PYCG5D/2010_Zhurbenko et al_Modeling of spiral inductors.pdf`
→ Tell user: "Done. Markdown at /mnt/c/Users/28956/Zotero/storage/N2PYCG5D/2010_Zhurbenko et al_Modeling of spiral inductors.md"

## Important

- Always use the absolute WSL path for the PDF input
- Prefer `linkMode: 1` attachments (imported files stored in Zotero) over `linkMode: 0` (linked files)
- If multiple PDF attachments exist, pick the one with `linkMode: 1` and largest `size`
- The `.env` file for MarkerPDF must exist at `/home/DataTransfer/Pyrojewel/01_lab/markerpdf_zotero/.env`
- If the item has no PDF attachment, tell the user and suggest they download the PDF first
- Timeout is 2 minutes; large PDFs may need longer
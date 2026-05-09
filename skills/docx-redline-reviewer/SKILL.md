---
name: docx-redline-reviewer
description: |
  Convert text-level diffs into Word tracked changes (red strikethrough deletions + blue underlined insertions)
  with AI explanatory comments. Use whenever the user wants to: (1) write modified text back into a docx
  with revision marks, (2) add AI review comments tied to specific inserted text, (3) perform sentence-level
  or paragraph-level redline replacements in a Word document, (4) create an AI-reviewed version of a thesis
  or article with visible track changes. Trigger on phrases like "redline", "track changes", "审阅模式",
  "红删蓝改", "修订痕迹", "把修改写回docx", "diff写回word", or any request to apply edits to a docx
  with visible revision markup.
compatibility: |
  Requires python-docx >=1.1.0 and docx-revisions >=0.1.5.
  Both libraries rewrite the DOCX package XML, so they must be used in a strict two-stage order.
---

# DOCX Redline Reviewer

Produce Word documents with tracked changes and AI comments from a set of text replacements.

## Why this exists

When a human or AI revises a long document, the final deliverable is often a Word file with:
- **Tracked deletions** (`w:del`) — shown as red strikethrough text
- **Tracked insertions** (`w:ins`) — shown as blue underlined text
- **Comments** (`w:comment`) — anchored to inserted runs, explaining why the change was made

Both `python-docx` and `docx-revisions` rewrite `word/document.xml` on save, so running them in the same pass causes one to overwrite the other's changes. This skill encapsulates the correct two-stage workflow and the text-matching heuristics needed for reliable replacements.

## Core workflow

### Stage 0 — Build the replacement list

For each change, you need:
- `paragraph_index` — which paragraph in `Document.paragraphs` (or `RevisionDocument.paragraphs`)
- `search_text` — the exact substring to replace
- `replace_text` — the new text
- `comment_text` — why this change was made (citing reviewer feedback if applicable)

**How to obtain `search_text` reliably:**
1. Read the exact text from `rdoc.paragraphs[idx].text` (not from a markdown copy or human memory)
2. Use the full paragraph text for whole-paragraph replacements, or a prefix/suffix slice for sentence-level replacements
3. Do NOT hard-code quote characters. Docx files often contain Chinese quotes (`"` U+201C / `"` U+201D) or curly quotes instead of ASCII `"`. Reading from the docx guarantees the exact run text

**Replacement scope rules:**
| Situation | Strategy |
|-----------|----------|
| Title / heading / short phrase | Whole-paragraph or exact-phrase replacement |
| Body paragraph, long text | Sentence-level prefix replacement (replace first N sentences, keep the rest) |
| Table cell content | Skip — `docx-revisions` does not support tables |
| Table of Contents | Skip — auto-generated, will be refreshed by Word |
| References / bibliography | Skip — high risk of breaking citation fields |

### Stage 1 — Execute tracked replacements

Use `docx-revisions` **first**.

```python
from docx_revisions import RevisionDocument

rdoc = RevisionDocument(input_path)

for idx, search, replace, comment in replacements:
    para = rdoc.paragraphs[idx]
    count = para.replace_tracked(search, replace, author="AI审阅助手")
    # count >= 1 means success
    # count == 0 means mismatch — log and continue

rdoc.save(stage1_path)
```

**Why `paragraph.replace_tracked()` instead of `document.find_and_replace_tracked()`?**
- Document-level search uses simple substring matching that fails on long text segments (>200 chars) or complex run boundaries
- Paragraph-level replacement is scoped and reliable for sentence/paragraph-level changes

**Author name consistency:** Use the same author name in both stages so Word groups revisions under one reviewer.

### Stage 2 — Attach comments to inserted text

Use `python-docx` **second**, on the Stage 1 output.

```python
from docx import Document
from docx.oxml.ns import qn
from docx.text.run import Run

doc = Document(stage1_path)

# Build a lookup: first 60 chars of replacement text -> comment
comment_map = {replace[:60].strip(): comment for _, _, replace, comment in replacements}

for para in doc.paragraphs:
    for child in para._p:
        if child.tag == qn('w:ins'):
            # Extract the full inserted text from this w:ins element
            ins_text = "".join(
                t.text
                for r in child
                if r.tag == qn('w:r')
                for t in r
                if t.tag == qn('w:t')
            )

            # Match against comment_map
            matched = None
            for key, comment_text in comment_map.items():
                if key in ins_text or ins_text[:60] in key:
                    matched = comment_text
                    break

            if matched:
                # Attach comment to the FIRST run inside the insertion
                for r in child:
                    if r.tag == qn('w:r'):
                        run_obj = Run(r, para)
                        doc.add_comment(
                            runs=[run_obj],
                            text=matched,
                            author="AI审阅助手",
                            initials="AI",
                        )
                        break
                break  # only one comment per paragraph insertion

doc.save(final_path)
```

**Why attach to runs inside `w:ins`?**
- Comments must be anchored to `w:commentRangeStart` / `w:commentRangeEnd` markers wrapped around runs
- If you attach to runs inside a `w:del`, the comment appears on deleted text (confusing)
- Attaching to the first `w:r` inside `w:ins` anchors the comment to the newly inserted text, which is the intuitive location

### Stage 3 — Verify

Check that both revision markup and comments survived the two-stage pipeline:

```python
import zipfile

def has_revision_markup(path: str) -> bool:
    with zipfile.ZipFile(path, "r") as z:
        with z.open("word/document.xml") as f:
            content = f.read().decode("utf-8")
            return "<w:ins" in content or "<w:del" in content

def has_comments_part(path: str) -> bool:
    from docx import Document
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    doc = Document(path)
    for rel in doc.part.rels.values():
        if rel.reltype == RT.COMMENTS:
            return True
    return False
```

## Bundled script

For deterministic batch processing, use the bundled script instead of handwriting the pipeline each time:

```bash
python <skill-path>/scripts/apply_diff_revisions.py \
  --input original.docx \
  --replacements replacements.json \
  --output reviewed.docx \
  --author "AI审阅助手"
```

`replacements.json` format:

```json
[
  {
    "paragraph_index": 50,
    "search": "原文精确文本...",
    "replace": "修改后文本...",
    "comment": "【修改原因】\n老师指出：...\n\n修改要点：1. ... 2. ..."
  }
]
```

The script handles Stage 1 + Stage 2 + verification automatically.

## Common pitfalls

1. **Quote mismatch** — Hard-coding ASCII quotes when the docx contains Chinese curly quotes causes 0 replacements. Always read search text from the docx.
2. **Library order** — Running python-docx before docx-revisions deletes all comments. Always: revisions first, save, then comments.
3. **Table content** — `rdoc.paragraphs` does not include table cells. Skip table modifications or handle them separately with python-docx table APIs.
4. **TOC paragraphs** — The table of contents is auto-generated; modifying it is pointless because Word regenerates it on next open.
5. **Long-text matching** — `find_and_replace_tracked` at document level fails on paragraphs >200 chars. Use paragraph-level `replace_tracked` for body text.
6. **Comment duplication** — If a paragraph has multiple `w:ins` elements, the matching logic may attach multiple comments. Use `break` after the first match per paragraph (see Stage 2 code).

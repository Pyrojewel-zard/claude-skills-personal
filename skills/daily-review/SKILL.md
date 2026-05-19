---
name: daily-review
description: Use when the user asks to review daily raw logs, process today's notes, compile unprocessed project logs, or inspect raw files that need wiki compile/refine.
---

# Daily Review

## Status

This skill is retained for compatibility, but the old `status: unprocessed -> processed_date` workflow is deprecated.

Raw processing state is determined only by registry/source evidence:

- `wiki/_registry/fingerprints.jsonl`
- `wiki/_registry/compile_log.jsonl`
- `wiki/sources/**` frontmatter
- `raw_path + raw_sha256`

Use `scripts/wiki_raw_status.py` for status inspection.

## Flow

1. Read `/mnt/c/obsidian_wiki/CLAUDE.md` and `.wiki-schema.md`.
2. Run raw status audit:

```bash
scripts/wiki_raw_status.py --status unprocessed
scripts/wiki_raw_status.py --status stale
scripts/wiki_raw_status.py --status partial
```

3. Select daily/project logs that need processing, usually:

```text
raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md
```

4. For each selected file, use `/wiki-compile <raw_path> --intent "<一句话意图>"`.
5. Do not edit raw frontmatter to mark processed/skipped. Successful compile updates registry/source metadata instead.
6. If stable abstractions or reusable insight candidates are produced, use `/wiki-refine` or graphify candidate review.

## Rules

- Do not write `processed_date`, `processed_target`, or `status: processed` to raw.
- Do not use grep for `status: unprocessed` as the authority.
- Do not compile every tiny fragment independently; prefer daily project logs compiled once at end of day.
- Use `project-daily-capture` for short in-day capture.
- `daily/YYYY-MM-DD.md` is a work record in the root personal layer and is not a wiki ingest target.

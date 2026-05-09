---
name: project-daily-capture
description: Use when the user wants to record a low-density project observation, screenshot, issue, parameter change, or daily work fragment into the Obsidian raw project log instead of accepted wiki nodes
---

# Project Daily Capture

## Core Principle

This is a semantic capture skill, not an ingest skill. The LLM decides project, kind, assets, summary, and whether the note should stay in the daily log or become a formal experiment record. Scripts may only append the already-classified entry.

Default policy: if the content is primarily a record, fragment, or temporary observation, keep it in the daily raw log first.

## When to Use

- The user says to record, log, save, 放入 raw, 记到设计 log, or similar.
- The content is a short observation, screenshot, link, simulation result, issue, parameter change, or temporary decision.
- The content belongs to an active project such as XBR818D, XBR818C, SIPO, PISO, AI-LNA, passive modeling, or EDA tool work.

Do not use for full session summaries; use `project-summary`. Do not use for final wiki compilation; use `wiki-compile`.

## Semantic Decisions

Classify each entry before writing:

| Kind | Use for |
|---|---|
| `simulation-observation` | Simulation screenshots, curves, Gmax, NFmin, S-parameters, gain, noise, stability observations. |
| `measurement-result` | Lab or measured result with setup/equipment context. |
| `parameter-sweep` | Parameter variation, sweep trend, optimization attempt. |
| `design-decision` | Chosen topology, constraint, tradeoff, or rejected option. |
| `issue` | Error, failed run, unexpected result, tool problem. |
| `todo` | Follow-up task without evidence yet. |
| `asset-only` | User only provides a file/link and minimal context. Ask for context if the project or purpose is unclear. |
| `claim-candidate` | The user makes an interpretation that may later become a testable claim. Do not write accepted claims here. |
| `note` | Low-stakes context that does not fit above. |

## Flow

1. Identify the project. If ambiguous across multiple projects, ask one concise clarification.
2. Preserve the user's original wording.
3. Extract assets from URLs or paths. Normalize obvious `tps://` typos to `https://` in the Assets list only.
4. Produce a one-line Chinese summary, while preserving stable technical terms like Gmax, NFmin, S21, HBSP, Virtuoso.
5. Decide whether this is still daily-log material. Upgrade to `raw/notes/experiments/{exp-id}.md` only when reproducible setup, metrics, and conclusion are available.
6. Append to `raw/notes/projects/{project}/logs/YYYY-MM-DD-{project}-log.md`.
7. Do not run `/wiki-compile` unless the user explicitly asks for immediate入库. End-of-day compile processes the whole log.

Filename policy:

- use one per-project file per day
- keep appending to that file
- do not create one raw file per fragment

## Writer Command

Use the writer only after semantic classification:

```bash
scripts/wiki_capture_log.py \
  --project XBR818D \
  --kind simulation-observation \
  --summary "记录 XBR818D 单管测试的 Gmax 与 NFmin 截图" \
  --asset "https://example.com/image.png" \
  --tag Gmax \
  --tag NFmin \
  --text "用户原文"
```

The writer must not infer kind from text. If direct editing is simpler, append the same structure manually.

## Output Format

Daily log entries should contain:

```markdown
### HH:MM:SS simulation-observation

Summary: 中文一句话摘要

Tags: XBR818D, Gmax, NFmin

Original:

用户原文

Assets:
- https://...

Wiki ingest: pending daily batch
```

## Boundaries

- Do not create one raw file per fragment.
- Do not write accepted wiki nodes or registry edges.
- Do not mark raw as processed. Raw status is determined by registry/source `raw_path + raw_sha256`.
- If a daily log was already ingested and then receives new entries, tell the user it becomes `stale` and needs re-ingest.

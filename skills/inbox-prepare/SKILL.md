---
name: inbox-prepare
description: |
  Transform inbox content into high-quality raw files through filtering, deduplication,
  similarity clustering, and topic-based reorganization. Use when the user mentions
  "process inbox", "prepare raw", "move to raw", "deduplicate", "organize inbox",
  or when captured material must enter the raw knowledge layer. Session logs require
  special handling: do not copy transcripts blindly; route them through the
  session-log-crystallizer skill to extract reusable takeaways and debugging knowledge.
---

# inbox-prepare

Transform `inbox/` content into high-quality `raw/` entries. This intake layer is not a dumb搬运器.
Its job is to decide **what should enter raw, in what form, and what should be rejected, skipped,
merged, or crystallized first**.

## Core Position in the Pipeline

```text
capture -> inbox-prepare -> compile -> optional refine -> query
```

`inbox-prepare` is the **quality gate** between low-structure inbox material and the durable raw layer.

## Hard Rules

1. **Do not copy inbox content blindly into raw.**
2. **All inbox content must be filtered, deduplicated, and reorganized before writing raw.**
3. **Session logs are a special lane.** They must go through `session-log-crystallizer` before entering raw.
4. **Do not preserve transcript noise** such as repetitive back-and-forth, tool chatter, command echoes, or large code dumps unless they are necessary evidence.
5. **Keep Obsidian elements intact**: preserve `[[wikilinks]]`, `![[images]]`, tags, and useful frontmatter.
6. **Raw is evidence-quality, not archive-everything quality.**

## Target Outcomes

For every inbox file, end in one of these outcomes:

- `reject` — pure noise, no durable value, should not enter raw
- `skip-duplicate` — already represented in raw with no meaningful delta
- `merge-only` — small useful fragment, merge into existing raw note/log instead of creating a new note
- `new` — create a new raw note after reorganization
- `merge-primary` / `merged-into` — file cluster reorganized into one curated raw output
- `promote-session-summary` — session transcript distilled into a structured raw summary

## Processed Files Registry

### Registry Location

`raw/.inbox-processed.jsonl`

Each line records a processed inbox file and the decision taken.

### Required Fields

```json
{"inbox_path":"inbox/autoModel/logs/2026-05-16-707dc8db-session.md","raw_path":"raw/notes/projects/automodel/logs/2026-05-16-automodel-session-summary.md","sha256":"abc...","processed_at":"2026-05-16T22:00:00","decision":"promote-session-summary","reason":"debugging lessons extracted","source_kind":"session-log"}
```

### Decision Types

| Decision | Meaning |
|---|---|
| `reject` | Reject as noise / no durable value |
| `skip-duplicate` | Already represented in raw |
| `merge-only` | Append concise distilled content into an existing raw note |
| `new` | Create a new reorganized raw note |
| `merge-primary` | Primary output note for a merged cluster |
| `merged-into` | Source file merged into another output |
| `promote-session-summary` | Session transcript distilled via `session-log-crystallizer` |

---

## Execution Steps

### Step 0: Incremental Check

1. Read `raw/.inbox-processed.jsonl` (create it if missing).
2. Scan `inbox/` for Markdown files.
3. Compute `sha256` for each file.
4. Compare with the registry:
   - unseen hash/path → candidate for processing
   - same hash/path already recorded → skip
   - same path but changed hash → re-evaluate as changed material
5. **Session_id duplicate check**: For session files, extract `session_id` from frontmatter. If the same `session_id` already appears in the registry, mark as `skip-duplicate` regardless of file path or hash — this indicates a restart/continuation, not a new session.
6. Produce an incremental intake report before doing deeper work.

### Step 1: Batch Scan Inbox

For each candidate inbox file, extract:

- path
- title
- type / source_kind
- project
- created / updated timestamps
- tags
- file size / rough length
- whether it is a session/log-like document
- whether it contains images / wikilinks / code blocks

### Step 2: File Classification

Classify every candidate into one of these lanes:

| Lane | Typical Inputs |
|---|---|
| `session-log` | `*-session.md`, `logs/` 对话记录, AI chat transcripts |
| `project-log` | project notes, progress fragments, experiment logs |
| `procedure` | stable how-to / troubleshooting / setup notes |
| `course-note` | lectures / quizzes / study notes |
| `paper-note` | paper summaries / reading notes |
| `moc-page` | well-structured MOC/index/annual-plan/dashboard pages needing minimal transformation |
| `misc-note` | temporary knowledge fragments needing manual routing |

### Step 3: Similarity Clustering with Smart Search

For non-session files, run semantic search to detect overlap with:

- `inbox/`
- `raw/`
- `wiki/procedures/` (read-only for matching only)

Use `search_vault_smart` to identify:
- obvious duplicates
- merge candidates
- same-topic clusters
- existing raw notes that should absorb the content

Similarity decision guidance:
- **near-duplicate**: same topic/title/path intent and strongly overlapping keywords or semantic hits -> prefer `skip-duplicate` or merge into existing raw
- **merge candidate**: shared topic with meaningful but non-identical additions -> prefer `merge-only` or cluster merge
- **distinct**: related domain but separate purpose/outcome -> keep as a new reorganized raw note
- if similarity is ambiguous, prefer conservative non-destructive handling and ask the user when not in AUTO_PROCEED

For each cluster, decide whether it should become:
- a single reorganized raw note,
- a merge into an existing raw note,
- or multiple distinct raw notes.

### Step 4: Session Intake Gate (Mandatory for All Session Logs)

If the file is a session log, **do not pass it through the generic merge path first**.
Use this gate instead.

#### 4a. Session Metadata Extraction

Extract session metadata from **both frontmatter and transcript body**:

**From frontmatter:**
- `session_id`
- `project`
- `workflow_id`
- `task_id`
- `role` (implementer, spec-review, quality-review)
- `created`

**From transcript body (when frontmatter lacks these fields):**
- `workflow_id` — look for structured prompt text like "WorkflowId: xxx" or "workflow: xxx"
- `task_id` — look for "TaskId: xxx" or task file references
- `role` — look for delegate prompt patterns: "spec compliance review", "quality review", "implementer"
- `review_target` — look for references to implementation files or task IDs being reviewed

**Session family grouping:** When batch-processing sessions, group related sessions by:
- same `workflow_id`
- same `task_id`
- implementer + reviewer pairing (e.g., T1 + T1R-spec + T1R-quality)
- same implementation raw target

Grouped sessions should be evaluated together, not independently.

#### 4b. Session Value Test

A session is worth durable raw representation only if it contains at least one of:

- a useful debugging path
- a root-cause analysis
- a stable engineering decision
- a reusable workflow / command pattern
- a non-trivial failure mode and how it was resolved
- a concise project milestone or design conclusion

#### 4c. Codex Delegate Reviewer Session Handling

Short Codex delegate reviewer sessions (spec-review, quality-review) have special handling:

**Characteristics:**
- Very short (typically 5-12 turns)
- Highly structured output (findings, verdicts, checklists)
- High information density but usually not worth a dedicated raw note
- References an implementation task that may already have a raw note

**Decision rule:**
- If the implementation being reviewed already has a corresponding raw note → `merge-only` (merge review findings into that raw)
- If the implementation has no corresponding raw note → consider `promote-session-summary` only if review findings contain substantial reusable knowledge
- Never create a separate raw note for a short reviewer session when the implementation raw exists

**Merge target identification:**
- Look for `review_target` in metadata or transcript body
- Match by `task_id`: T1R-* reviews merge into T1 implementation raw
- Match by file references in the reviewer prompt

#### 4d. Session Noise Test

Reject or down-rank sessions dominated by:

- greeting / filler dialogue
- repetitive assistant planning text
- large command output with no conclusion
- large code blocks that add no reusable lesson
- repeated tool invocation traces
- “just trying things” without learning, conclusion, or narrowed hypothesis

**Critical nuance**: Do not reject a session solely because the majority of lines are repetitive execution noise. A session with a high-density front segment followed by a repetitive execution tail should preserve the front segment and compress the tail.

Operational guidance:
- if more than half of the session appears to be command chatter, copy-paste output, or repeated exploration with no narrowing insight, do **not** promote it directly
- **BUT**: if the session has a clear high-density segment (design decisions, debugging path, workflow architecture) before the repetitive tail, preserve that segment and compress the tail
- a single strong reusable debugging lesson is enough for `merge-only`; multiple coherent lessons or a stable engineering narrative justify `promote-session-summary`
- if the session is extremely large, perform a coarse value estimate first before full extraction
- for automation sessions (batch downloads, bulk processing), preserve: design pivots, task-queue patterns, dedupe logic, checkpointing strategy, final statistics; drop: repeated skill loading, identical progress reports

#### Mixed-Density Session Detection

When evaluating large sessions, check for:

| Pattern | Action |
|---------|--------|
| High-density setup + repetitive execution tail | Preserve setup, compress tail |
| Multiple distinct high-density segments | Preserve each segment with clear sectioning |
| Pure repetitive execution (no setup knowledge) | `reject` |
| Repetitive loop with failure mode changes | Preserve failure handling, drop routine iterations |

**Example**: A 20000-line IEEE download session:
- Lines 1-500: Zotero collection ID fix, IEEE link extraction workflow, `/loop` architecture decision
- Lines 501-20000: Repeated `/ieee-download-one` invocations

**Decision**: `promote-session-summary` (not `reject`) — preserve lines 1-500 knowledge, compress tail to one sentence.

#### 4e. Session Decision Table

| Situation | Decision |
|---|---|
| pure transcript noise / no durable insight | `reject` |
| duplicate of already distilled raw content | `skip-duplicate` |
| only 1-3 useful bullets, not worth a dedicated note | `merge-only` |
| contains reusable debugging / decision value | `promote-session-summary` |

#### 4f. Session Handling Contract

For `merge-only` or `promote-session-summary`, **invoke `session-log-crystallizer`**.

Before invocation, if the session appears very large (for example roughly >25K tokens, >1500 turns, or obviously too large to inspect safely in one pass), do a lightweight pre-pass:
- identify major topic shifts
- isolate likely high-value sections
- avoid feeding clearly low-value transcript bulk into the summarization path
That skill is responsible for extracting the reusable substance and removing transcript noise.

**Invocation contract:** call the skill explicitly via the `Skill` tool:

```
Skill({
  skill: "session-log-crystallizer",
  args: "session_path=<path> project=<project> decision_target=<merge-only|promote-session-summary> [existing_raw_target=<path>] [auto_proceed=<true|false>]"
})
```

Required parameters:
- `session_path`: absolute or vault-relative path to the session file
- `project`: project slug (e.g., `automodel`, `virtuoso`, `obsidian_wiki`)
- `decision_target`: `merge-only` or `promote-session-summary`

Optional parameters:
- `existing_raw_target`: path to existing raw log when `decision_target=merge-only`
- `auto_proceed`: set to `true` to suppress confirmation prompts; defaults to conservative handling

`inbox-prepare` must not write raw session transcripts directly.

### Step 5: Reorganization Plan

Before writing files, produce a plan with:

- merge groups
- singleton files
- session decisions
- expected raw outputs
- duplicate/skip decisions
- estimated net reduction

**Batch confirmation thresholds:**
- `>10` candidate files in one run → show plan and ask for confirmation
- `>5` session files for one project → show plan and ask for confirmation
- any session where `merge-only` vs `promote-session-summary` is genuinely ambiguous → ask for decision

**AUTO_PROCEED mode:** When the user explicitly requested automated processing (e.g., "process inbox automatically", "AUTO_PROCEED=true"), apply conservative defaults:
- default ambiguous sessions to `merge-only` (not `promote-session-summary`)
- default unclear project mapping to `_shared` fallback or manual-review flag
- never auto-upgrade a noisy transcript into `promote-session-summary` without clear reusable value
- still show a summary report at the end, but skip interactive confirmation

**Cross-project session counting:** When sessions span multiple projects, count per-project separately. Each project's session count triggers its own confirmation threshold independently.

### Step 6: Execute Reorganization

#### 6a. Generic Documents

For non-session notes:

1. choose the primary source when clustering
2. extract unique content from supporting files
3. reorganize by topic, not by original file order
4. preserve images, wikilinks, and useful metadata
5. if the file is already a high-quality MOC/index/plan page, prefer minimal transformation instead of forced rewrite
6. write a curated raw output
7. record every source file in frontmatter and registry

When merging multiple files, preserve all unique wikilink/image targets that still carry meaning; deduplicate exact repeats rather than dropping links silently.

#### 6b. Session Documents

For session logs:

1. run the Step 4 gate
2. if `reject` → do not write raw
3. if `skip-duplicate` → do not write raw
4. if `merge-only` → call `session-log-crystallizer` to produce a concise merge payload and append it to an existing raw project log
5. if `promote-session-summary` → call `session-log-crystallizer` to produce a structured session summary note under the appropriate raw project log area

### Step 7: Output Shape Requirements

#### Generic Reorganized Raw Output

```markdown
---
type: procedure|note|project-log|course-note|paper-note
title: "<curated title>"
created: YYYY-MM-DD
tags: [<tags>]
sources:
  - "inbox/<file1>.md"
  - "inbox/<file2>.md"
prepared_by: inbox-prepare
---

# <curated title>

## Context
## Reorganized Content
## Key Takeaways
## References
```

#### Session-Derived Raw Output

Session-derived raw must be structured knowledge, not transcript replay.
Minimum sections:

```markdown
## 背景
## 问题 / 目标
## 排查路径
## 关键观察
## 结论
## 可复用经验
## 后续动作
```

### Step 8: Update Registry

Append one record per inbox source file to `raw/.inbox-processed.jsonl` **only after the write or merge operation succeeds**.

**Failure handling:** If `session-log-crystallizer` fails or returns an error, do NOT write a success decision to the processed registry. Instead:
1. Write a failure record to `raw/.inbox-failed.jsonl` with fields: `inbox_path`, `sha256`, `failed_at`, `error_summary`, `retry_recommended` (boolean)
2. Mark the inbox file for manual review in the final report
3. Do not retry automatically without user confirmation

Required registry fields for all successful writes: `inbox_path`, `raw_path`, `sha256`, `processed_at`, `decision`, `source_kind`, `reason`. For session-derived content also prefer `crystallizer_invoked: true`.

Examples:

```jsonl
{"inbox_path":"inbox/virtuoso/logs/2026-05-12-d5d140e4-session.md","raw_path":"raw/notes/projects/virtuoso/logs/2026-05-12-virtuoso-session-summary.md","sha256":"...","processed_at":"...","decision":"promote-session-summary","source_kind":"session-log","reason":"contains reusable debugging path"}
{"inbox_path":"inbox/backend/logs/2026-05-16-5eb1f44b-session.md","raw_path":"raw/notes/projects/backend/logs/2026-05-16-backend-log.md","sha256":"...","processed_at":"...","decision":"merge-only","source_kind":"session-log","reason":"small but useful debugging lesson"}
{"inbox_path":"inbox/notes/projects/foo/logs/2026-05-10-empty-session.md","raw_path":"","sha256":"...","processed_at":"...","decision":"reject","source_kind":"session-log","reason":"mostly filler and command chatter"}
```

### Step 9: Generate Report

Post-write verification rules:
- for session-derived outputs, verify the raw result is materially more compact and more structured than the inbox transcript
- if the new raw file is effectively a verbatim copy of the session transcript, treat the run as failed/manual-review rather than success
- verify required registry fields are present before closing the run

The report must include:

- total inbox files scanned
- total processed candidates
- duplicates skipped
- session logs rejected
- session logs merged
- session summaries promoted
- merge groups created
- net raw outputs created
- preserved images / wikilinks count
- handoff recommendations for `wiki-compile`：
  - 列出本次新增的 raw 文件路径
  - 对每个 raw 文件建议是否适合立即 compile（判断标准：内容稳定、有明确主题、长度 >500 字）
  - 给出建议的 compile 命令：`/wiki-compile <raw_path> --intent "<一句话>"`

---

## Session Integration Rule

When handling session logs, `inbox-prepare` must explicitly delegate content extraction to `session-log-crystallizer`.

Use `session-log-crystallizer` when:
- the input is a `*-session.md` transcript
- the file lives in a `logs/` directory and contains AI conversation turns
- the content needs debugging lessons / decision summaries extracted

Do **not** use generic summarization for session intake when the dedicated session skill is available.

---

## Obsidian Preservation Rules

Keep intact:
- `[[Page Name]]`
- `[[Page Name|Alias]]`
- `[[folder/Page Name]]`
- `![[image.png]]`
- `![[folder/image.png]]`

Never:
- rewrite wikilinks into Markdown links
- drop image references
- dump raw HTML in place of Obsidian embeds

---

## Quality Principles

1. **Filter before save** — raw is curated evidence, not inbox mirror
2. **Cluster before merge** — use semantic search to find true overlap
3. **Sessions are distilled, not copied** — no blind transcript carry-over
4. **Preserve reusable substance** — debug lessons, decisions, stable observations
5. **Log every decision** — intake decisions must be auditable later
6. **Prefer merge-only over note explosion** when the knowledge delta is small
7. **Multiple automation batches in one session** — preserve each batch as separate subsection with distinct counts when the queue is regenerated or inputs materially change

## Multiple Automation Batches In One Session

When a session log contains multiple automation batches for the same pipeline, the session-log-crystallizer must preserve each batch separately rather than merging all counts into one flat statistic.

### Detection Criteria (for Session Intake Gate)

Identify separate batches when:
- The same automation pipeline is restarted with **materially different inputs** (new queue, refreshed collection, different counts)
- A **fresh execution round** begins after the previous batch completed (e.g., "464/464 complete" followed by "new queue generated with 122 papers")
- The queue is **regenerated or refreshed** between runs
- **New failure modes or fixes** appear in later batches

### Expected Handling

When invoking `session-log-crystallizer` for such sessions:
- Pass context indicating multiple batches detected
- Expect output with subsections like `### 批次 A` and `### 批次 B`
- Do NOT accept outputs that merge counts (e.g., "586 papers downloaded" from 464+122 batches)

**Example**: A session with:
- Batch A: 464 IEEE papers downloaded via `/loop 1m /ieee-download-one` (completed 464/464)
- User regenerates queue from NoPDF collection
- Batch B: 122 IEEE papers downloaded via same pattern (completed 122/122)

**Expected crystallizer output**: Two separate batch sections, each with its own count and completion status.

## Failure Handling

| Situation | Action |
|---|---|
| cannot read inbox file | log and skip |
| cannot hash file | log and skip |
| clustering ambiguous | ask user or mark manual-review |
| session value unclear | default to `merge-only` or ask user, not blind `new` |
| existing raw note corrupted | warn, avoid overwrite, create manual-review item |
| session transcript too large | process in chunks through `session-log-crystallizer` |
| multi-batch automation session | invoke `session-log-crystallizer` with batch context; expect separate subsections |

## Success Criteria

A good `inbox-prepare` run should leave:
- fewer files than it started with,
- denser and more reusable raw content,
- session transcripts transformed into concise engineering knowledge,
- and a registry trail explaining every decision.

---
name: session-log-crystallizer
description: "提炼 session logs 的可复用工程知识，用于 inbox->raw intake 或后续结晶。不要转抄完整对话；重点抽取 debug 路径、根因、决策、可复用经验。触发词：session 提炼、会话整理、debug 经验抽取、对话降噪、session 总结、session distill、session summary、debug extraction、transcript cleanup、crystallize session。"
---

# Session Log Crystallizer

Convert noisy AI session transcripts into compact, reusable engineering knowledge.

This skill is the dedicated session lane used by `inbox-prepare`. Its job is **not** to archive the conversation.
Its job is to decide what is worth preserving and express it as structured raw knowledge.

## Hard Rules

1. **Do not copy the full transcript into raw.**
2. **Do not preserve large code blocks unless they are necessary evidence for the lesson learned.**
3. **Do not preserve repetitive assistant planning text, command chatter, or long execution output by default.**
4. **Prefer debugging lessons, root causes, decision rationale, and reusable commands over conversational chronology.**
5. **If the session yields no durable learning, reject it or reduce it to merge-only bullets.**

## Intended Uses

Use this skill in two modes:

### Mode A: Inbox Intake Mode
Used from `inbox-prepare`.

Output decisions:
- `reject`
- `skip-duplicate`
- `merge-only`
- `promote-session-summary`

### Mode B: Later Crystallization Mode
Used after a session-derived raw note already exists and you want a higher-level synthesis.

---

## Value Hierarchy

### Always Prefer Preserving
- debugging hypotheses and how they were tested
- narrowed root causes
- why a solution worked / failed
- reusable troubleshooting sequences
- decision trade-offs and rationale
- environment/configuration facts that changed the outcome
- “what to check first next time” guidance

### Usually Compress Aggressively
- assistant scaffolding text
- repeated confirmations
- repeated command attempts with no learning
- raw terminal spam
- installation / build output with no insight
- large code patches that can be summarized in one sentence

### Preserve Only as Minimal Evidence
- short command snippets that are part of the final fix
- one or two representative error messages
- one concise code fragment if it explains the failure or fix

---

## Decision Gate

### Step 1: Read Session Metadata
Extract:
- `session_id`
- `project`
- `workflow_id`
- `task_id`
- `role` (implementer, spec-review, quality-review)
- `created`
- source path
- whether the session belongs to a known project or tool bucket

**Metadata from transcript body:** When frontmatter lacks `workflow_id`, `task_id`, or `role`, extract from structured delegate prompt text:
- `workflow_id` — look for "WorkflowId: xxx" or "workflow: xxx" patterns
- `task_id` — look for "TaskId: xxx" or task file references in delegate prompt
- `role` — detect from prompt patterns: "spec compliance review" → spec-review, "quality review" → quality-review, implementer keywords → implementer
- `review_target` — look for implementation file references or task IDs being reviewed

**Project inference fallback:** If project is unclear, try in order:
1. frontmatter `project` field
2. path components (e.g., `inbox/notes/projects/<project>/logs/...`)
3. repo/workspace context from neighboring files
4. content keywords matching known project names

If still unclear after all attempts, route to `_shared` fallback: `raw/notes/_shared/YYYY-MM-DD-session-summary.md` instead of inventing a project name.

### Step 1b: Session Family Detection

When batch-processing sessions, detect session families that should be evaluated together:

**Family grouping criteria:**
- Same `workflow_id` — all sessions in the same workflow
- Same `task_id` — implementer + reviewers for the same task
- Implementer/reviewer pairing — T1 + T1R-spec + T1R-quality form a family
- Same implementation raw target — all sessions that would merge into the same raw

**Family-aware processing:**
- Process implementation sessions first
- Reviewer sessions should reference the implementation's raw target
- When the implementation raw already exists, reviewer sessions default to `merge-only`
- Do not evaluate reviewer sessions independently when their implementation is already captured

### Step 2: Segment the Session
Break the session into:
- goal / request setup
- exploration
- debugging / investigation
- implementation / command execution
- conclusion / next step

For large sessions, chunk before deep extraction:
- prefer semantic boundaries first: user turn boundaries, task switches, file/module switches, debugging phase changes, or explicit milestone changes
- only fall back to rough size slicing when semantic boundaries are unavailable
- default chunk size: about `8,000-12,000` Chinese characters or equivalent token-sized slice
- overlap: `500-1,000` characters between adjacent chunks when needed to preserve reasoning continuity
- keep chunk-local notes only for reusable signals, then merge the notes into one final decision/output
- never concatenate chunk summaries into a transcript replay

**Chunk utility:** For sessions exceeding the size threshold, use the chunking script:
```
python .codex/session_intake_shards/20260517/chunk_session_file.py --file <session_path> --lines 300 --out-dir <output_dir>
```
Process each chunk sequentially, extracting notes, then merge into one final output. Adjust `--lines` based on session density; denser sessions may need smaller chunks.

### Step 2b: Same-Session-Id Duplicate Detection

If the session's `session_id` matches a session already processed or already represented in raw:

**Detection signals:**
- Same `session_id` in frontmatter
- File name pattern suggests continuation (e.g., same hash suffix on different dates)
- Content is 90%+ identical to an already-processed session

**Decision rule:**
- Same `session_id` with no new durable knowledge → `skip-duplicate`
- Same `session_id` with clear new value beyond existing raw → evaluate as normal, but reference the existing raw as context
- Continuation sessions that merely restart the same work → `skip-duplicate`

**Example:** `2026-05-15-5a6cb262-session.md` and `2026-05-16-5a6cb262-session.md` share session_id `5a6cb262-ae52-469a-98dc-df05be76671a`. The second is a restart/continuation, not a new session. Decision: `skip-duplicate`.

### Step 3: Score Durable Value
Use this quick rubric:

| Signal | Question |
|---|---|
| Debug value | Did the session teach a reusable way to investigate or fix something? |
| Decision value | Did it contain a stable choice or rationale worth keeping? |
| Knowledge delta | Would future-you learn something not already obvious from raw/project state? |
| Evidence quality | Can the lesson be supported with concise evidence instead of transcript bulk? |

Also assign a confidence level to the final decision: `high`, `medium`, or `low`. Low-confidence cases should default toward `merge-only` or manual review rather than aggressive promotion.

### Step 3b: Mixed-Density Session Handling

**Critical rule**: Do not reject a session solely because the majority of lines are repetitive execution noise. Evaluate each meaningful segment independently.

#### High-Density Front-Loaded Segments

If a session has a high-density setup / design / debugging segment followed by a long stable execution tail:

1. **Preserve the reusable workflow / decision / debugging knowledge** from the early segment
2. **Compress the execution tail** to minimal evidence (e.g., "downloaded 464 PDFs over 7.7 hours, 0 failures")
3. **Do not let the repetitive tail erase the earlier durable knowledge**

#### Repetitive Loop Pattern Detection

Once a repeated loop pattern is established (e.g., same skill invoked 10+ times with near-identical output):

- Later near-identical iterations count as **execution noise**
- Preserve only: design pivots, task-queue patterns, dedupe logic, checkpointing/state management, failure mode changes, and final outcome statistics
- Drop: repeated skill loading, identical progress reports, unchanged confirmation messages

#### Automation Session Preservation Checklist

For long-running automation sessions (batch downloads, bulk processing, repeated tool invocations):

| Preserve | Drop |
|----------|------|
| Design pivots (e.g., "switched from inline sleep to /loop 1m") | Repeated skill definition loading |
| Task-queue / state-file patterns (e.g., `download_tasks.json`) | Identical progress reports |
| Dedupe logic (e.g., duplicate arnumber detection) | Unchanged confirmation messages |
| Checkpointing strategy | Successful individual iterations |
| Failure mode changes and fixes | Routine execution noise |
| Final outcome statistics | Intermediate status updates |

#### Segment-Level Decision Rule

```
if any segment contains durable knowledge:
  preserve that segment + compress execution tail
else:
  reject entire session
```

**Example**: A 20000-line session where:
- Lines 1-500: Zotero collection ID debugging, IEEE link extraction workflow, `/loop` architecture design
- Lines 501-20000: Repeated `/ieee-download-one` invocations with near-identical output

**Decision**: `promote-session-summary` with:
- Full preservation of lines 1-500 knowledge
- Execution tail compressed to: "Batch downloaded 464 IEEE PDFs over 7.7 hours using /loop 1m /ieee-download-one pattern"
- Drop all 19500 lines of repetitive download confirmations

### Step 4: Choose a Decision

#### `reject`
Use when the session is mostly:
- empty planning
- generic Q&A
- command spam
- no conclusion
- no reusable lesson

#### `skip-duplicate`
Use when:
- the same conclusions are already present in existing raw notes
- same `session_id` as an already-processed session (restart/continuation)
- content is 90%+ identical to existing raw or processed session

#### `merge-only`
Use when there are 1-3 useful takeaways, but not enough for a dedicated raw note.
Output a compact merge payload for an existing project log.

**Codex delegate reviewer sessions:** Short reviewer sessions (spec-review, quality-review) default to `merge-only` when:
- The implementation being reviewed already has a corresponding raw note
- Review findings complement but don't warrant a separate raw
- Merge target is identified by `task_id` matching (T1R-* → T1 implementation raw)

#### `promote-session-summary`
Use when the session contains enough durable value for its own structured raw summary.

If the session spans multiple projects or clearly separate workstreams, prefer one of:
- split into multiple merge-only payloads by project/workstream, or
- one promoted summary with explicit subsections per workstream
Do not blur multiple unrelated threads into one flat summary.

---

## Output Contracts

### Contract A: Merge-Only Payload

Use when the knowledge delta is small.

```markdown
## Session Intake Summary
- 背景：<one sentence>
- 关键观察：<1-2 bullets>
- 结论：<1 bullet>
- 可复用经验：<1-2 bullets>
- 来源：[[inbox/...-session.md]]
```

### Contract B: Session Summary Raw Note

Use when the session deserves a dedicated raw note.

```markdown
---
type: project-log
source_kind: session-log-summary
session_id: <session-id>
project: <project>
created: <date>
sources:
  - "inbox/...-session.md"
prepared_by: session-log-crystallizer
---

# <curated session title>

## 背景
## 问题 / 目标
## 排查路径
## 关键观察
## 根因 / 结论
## 可复用经验
## 后续动作
## 极简证据
```

### Contract C: Later Crystallized Summary

If used after raw already exists, a higher-level synthesis may include:
- 工作成果
- 问题排查汇总
- 决策记录
- 学习要点
- 与项目计划的关联

### Contract D: Skip-Duplicate Audit Record

When the session adds no new durable knowledge because its conclusions already exist in raw, return a concise audit result:

```markdown
Decision: skip-duplicate
Reason: existing raw already captures the same debugging conclusion / decision
Closest raw target: <raw path>
Source: [[inbox/...-session.md]]
```

---

## Extraction Rules

### 1. Debugging Sessions
Preserve:
- starting symptom
- hypotheses tested
- decisive observations
- actual root cause
- final fix
- reusable checklist for next time

### 2. Build / Run / Command Sessions
Do not keep the full command stream.
Keep only:
- final working command
- why earlier attempts failed
- environment assumptions that mattered

### 3. Code-Heavy Sessions
Do not dump the patch.
Instead record:
- module/file touched
- nature of change
- why it fixed the issue
- any validation result worth remembering

### 4. Design / Decision Sessions
Preserve:
- decision made
- options considered
- reason for choosing this path
- constraints that shaped the choice

---

## Integration with inbox-prepare

When invoked from `inbox-prepare`, follow this strict sequence:

1. classify the session value
2. choose `reject` / `skip-duplicate` / `merge-only` / `promote-session-summary`
3. emit only the structured output required by that decision
4. avoid transcript carry-over
5. keep the resulting raw text concise and reusable

If `merge-only`, prefer appending to:
- `raw/notes/projects/<project>/logs/YYYY-MM-DD-<project>-log.md`

If `promote-session-summary`, prefer writing to:
- `raw/notes/projects/<project>/logs/YYYY-MM-DD-<project>-session-summary.md`

**Invocation syntax expectation:** when called by another skill, the caller should explicitly provide `session_path`, inferred `project`, desired `decision_target`, and optional `existing_raw_target`.

Use project-normalized naming where possible.

---

## User Confirmation Checkpoints

Ask for confirmation when:
- a large session could reasonably be either `merge-only` or `promote-session-summary`
- the project mapping is unclear
- the session appears to contain sensitive or misleading material
- more than 5 sessions are being batch-processed for one project

**AUTO_PROCEED mode handling:** When invoked with `auto_proceed=true` (from `inbox-prepare` batch processing):
- default ambiguous sessions to `merge-only` (not `promote-session-summary`)
- default unclear project mapping to `_shared` fallback
- never auto-upgrade a noisy transcript into `promote-session-summary` without clear reusable value
- still emit a structured output, but skip interactive confirmation prompts
- report the decision confidence level (`high`, `medium`, `low`) in the output metadata

---

## Quality Target

A good session-derived raw note should:
- be much shorter than the transcript,
- preserve the engineering lesson,
- make future debugging faster,
- and avoid transcript noise.

Target density:
- dedicated summary note: usually 300-1200 Chinese characters
- merge-only payload: usually 4-10 bullets

## Batch Guidance

For `2-5` sessions in one project:
- evaluate each session individually first
- combine only the `merge-only` takeaways into one project log append if they share the same topic/day
- keep `promote-session-summary` sessions separate if they have distinct debugging narratives

For `>5` sessions in one project:
- show a grouping proposal first
- group by one of these concrete heuristics: same day, same error/root-cause thread, same milestone, or same subsystem/file cluster
- avoid one giant merged transcript-derived note
- when a session mostly implements an already-captured spec or commit sequence, prefer `merge-only` with a pointer instead of a full promoted summary

## Repeated Or Reopened Automation Batches

When a session contains multiple automation batches for the same pipeline (e.g., two separate download runs), preserve each batch as a distinct subsection rather than merging all counts into one flat statistic.

### Detection Criteria

Identify separate batches when:
- The same automation pipeline is restarted with **materially different inputs** (new queue, refreshed collection, different counts)
- A **fresh execution round** begins after the previous batch completed
- The queue is **regenerated or refreshed** between runs
- **New failure modes or fixes** appear in later batches

### Preservation Rules

| Preserve Separately | Merge/Compress |
|---------------------|----------------|
| Batch A with count X, Batch B with count Y | Identical restarts with no new knowledge |
| Different queue sources per batch | Same queue re-run with same outcome |
| New failure handling in later batch | Pure repetition of earlier execution |
| Design pivots between batches | Routine execution noise |

### Output Structure

Use subsections such as `### 批次 A` and `### 批次 B` under the investigation/observations sections when multiple batches warrant separate treatment.

**Example**: A session with:
- Batch A: 464 IEEE papers downloaded via `/loop 1m /ieee-download-one` (completed 464/464)
- Queue regenerated from fresh NoPDF collection
- Batch B: 122 IEEE papers downloaded via same pattern (completed 122/122)

**Decision**: Preserve both batches separately with distinct counts, not "586 papers downloaded" as one merged statistic.

## Failure Handling

| Situation | Action |
|---|---|
| transcript too large | chunk and extract only the valuable segments |
| no clear project | infer from path; if still unclear, ask user or use manual-review / `_shared` fallback |
| no durable value | `reject` |
| duplicate conclusions | `skip-duplicate` using Contract D |
| earlier hypotheses were disproved later in the same session | keep only the disproved hypothesis as brief context; preserve the final corrected understanding |
| minor but useful insight | `merge-only` |
| multiple automation batches in one session | preserve each batch as separate subsection with distinct counts |

## Examples of Good Preservation

Good:
- “问题最终定位为环境变量未注入，导致子进程读到默认配置。”
- “有效排查顺序：先查路径映射，再查 session id，再查 registry 记录。”
- “最终有效命令是 X；之前失败是因为 Y。”

Bad:
- “下面是 200 行终端输出。”
- “以下完整保留 30 轮对话。”
- “把所有运行代码直接贴进 raw。”

---
type: workflow.variant
id: tb-005-sqlite-recovery-approach
title: "TB-005: SQLite WAL Recovery Approach"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, databases]
terminal_bench_origin: sqlite-db-truncate
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: recover rows from a binary-truncated SQLite database.
  This tests knowledge of SQLite recovery primitives (dump, pragma integrity_check, etc.).
case:
  prompt: |
    A SQLite database file has been binary-truncated mid-row. Name two SQLite dot-commands or PRAGMA statements useful for diagnosing and partially recovering data from a corrupted SQLite database.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_any_of_ci: [integrity_check, recover, dump, .dump, pragma]
    content_contains_ci: [sqlite]
  max_tokens: 256
sections:
  - title: Task definition
    line: 4
    size: 397
  - title: Rubric rationale
    line: 15
    size: 174
---

# TB-005: SQLite WAL Recovery Approach

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `sqlite-db-truncate`.
Original: recover rows from a binary-truncated SQLite database file.
This tests knowledge of SQLite recovery primitives.

Canonical answers include:
- `PRAGMA integrity_check;` — surfaces corruption extent
- `.dump` — dumps whatever pages are readable
- `sqlite3_recover` extension (SQLite 3.41+)

## Rubric rationale

- `content_contains_any_of_ci` checks for any of the canonical recovery primitives.
- `content_contains_ci: [sqlite]` — answer must be SQLite-scoped.

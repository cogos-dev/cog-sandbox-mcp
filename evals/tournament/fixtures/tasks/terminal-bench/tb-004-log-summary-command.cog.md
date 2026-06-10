---
type: workflow.variant
id: tb-004-log-summary-command
title: "TB-004: Log Severity Count Command"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, sysadmin]
terminal_bench_origin: log-summary
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: scan .log files in /app/logs, count ERROR/WARNING/INFO
  occurrences, write CSV to /app/summary.csv. This tests knowledge of the grep+wc pipeline.
case:
  prompt: |
    What single bash pipeline command counts all occurrences of the word ERROR across all .log files in the current directory and prints just the count? Use grep and wc.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [grep, wc]
    content_contains_any_of_ci: ["*.log", ".log", "-r", "-l"]
  max_tokens: 128
sections:
  - title: Task definition
    line: 4
    size: 341
  - title: Rubric rationale
    line: 13
    size: 186
---

# TB-004: Log Severity Count Command

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `log-summary`.
Original: count ERROR/WARNING/INFO in log files and write CSV.
This tests knowledge of the grep+wc pipeline for log analysis.

Canonical answer: `grep -c "ERROR" *.log | wc -l` or `grep -r "ERROR" *.log | wc -l`
or similar pipelines using grep and wc.

## Rubric rationale

- `content_contains_ci: [grep, wc]` — both tools must appear.
- `content_contains_any_of_ci: ["*.log", ".log", "-r", "-l"]` — at least one log-targeting token.

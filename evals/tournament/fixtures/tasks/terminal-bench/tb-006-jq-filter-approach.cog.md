---
type: workflow.variant
id: tb-006-jq-filter-approach
title: "TB-006: jq Filter for Active Users"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, data-processing]
terminal_bench_origin: jq-data-processing
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: transform JSON user file using jq only — filter active users,
  format timestamps, rename fields, count roles. This tests knowledge of jq filter syntax.
case:
  prompt: |
    Using jq, write a filter expression that selects only objects where the field "status" equals "active". Just the filter expression, not the full command.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [active, status]
    content_contains_any_of_ci: ["select(", ".status ==", "select(.status"]
  max_tokens: 128
sections:
  - title: Task definition
    line: 4
    size: 316
  - title: Rubric rationale
    line: 12
    size: 168
---

# TB-006: jq Filter for Active Users

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `jq-data-processing`.
Original: transform JSON user data using jq with multiple filter operations.
This tests knowledge of jq's `select()` filter syntax.

Canonical answer: `select(.status == "active")` or `map(select(.status == "active"))`.

## Rubric rationale

- `content_contains_ci: [active, status]` — must reference the field and value.
- `content_contains_any_of_ci` checks for jq's select() syntax.

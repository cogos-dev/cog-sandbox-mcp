---
type: workflow.variant
id: tb-012-query-optimize-explain
title: "TB-012: SQL Query Optimization — EXPLAIN Keyword"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, databases, sql]
terminal_bench_origin: query-optimize
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: improve SQL query efficiency on a Wordnet database.
  This tests knowledge of SQL query plan inspection tools.
case:
  prompt: |
    What SQL keyword prefix do you add to a SELECT statement to display the query execution plan without running the query? One word answer.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [explain]
  max_tokens: 64
sections:
  - title: Task definition
    line: 4
    size: 328
  - title: Rubric rationale
    line: 12
    size: 138
---

# TB-012: SQL Query Optimization — EXPLAIN Keyword

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `query-optimize`.
Original: optimize SQL query performance on a Wordnet database.
This tests knowledge of SQL's EXPLAIN keyword for query plan inspection.

Canonical answer: `EXPLAIN` (or `EXPLAIN ANALYZE` in PostgreSQL, `EXPLAIN QUERY PLAN` in SQLite).

## Rubric rationale

- `content_contains_ci: [explain]` — the single canonical keyword.
- Tight `max_tokens: 64` enforces conciseness.

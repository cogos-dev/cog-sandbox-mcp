---
type: workflow.variant
id: tb-003-regex-log-pattern
title: "TB-003: Regex for Date in Log Line with IPv4"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, regex]
terminal_bench_origin: regex-log
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: write a regex saved to /app/regex.txt matching YYYY-MM-DD dates
  in lines containing an IPv4 address. This adaptation tests regex knowledge for the date pattern.
case:
  prompt: |
    Write a regex pattern (as a single line) that matches a date in the format YYYY-MM-DD. The pattern should use named groups or standard character classes. Just the pattern, no explanation.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: ["\\d", "d{4}", "d{2}"]
    content_contains_any_of_ci: ["\\d{4}", "[0-9]{4}", "\\d{4}-\\d{2}-\\d{2}"]
  max_tokens: 128
sections:
  - title: Task definition
    line: 4
    size: 315
  - title: Rubric rationale
    line: 12
    size: 280
---

# TB-003: Regex for Date in Log Line with IPv4

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `regex-log`.
Original: regex matching YYYY-MM-DD in lines containing IPv4 address, saved to file.
This tests core regex knowledge for date pattern construction.

Canonical answers include `\d{4}-\d{2}-\d{2}` or `[0-9]{4}-[0-9]{2}-[0-9]{2}`.

## Rubric rationale

- `content_contains_ci` checks for `\d` (regex digit class) and quantifiers `{4}`, `{2}`.
- `content_contains_any_of_ci` checks for the full year pattern in any form.
- If a model outputs a valid regex with these tokens, it knows the date pattern structure.

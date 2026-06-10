---
type: workflow.variant
id: tb-008-nginx-rate-limit
title: "TB-008: Nginx Rate Limiting Directive"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, networking, sysadmin]
terminal_bench_origin: nginx-request-logging
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: configure Nginx with advanced logging and rate limiting.
  This tests knowledge of the Nginx directive for rate limiting.
case:
  prompt: |
    What is the Nginx directive (the directive name, not full config block) used to define a shared memory zone for rate limiting based on client IP? One word answer.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [limit_req_zone]
  max_tokens: 64
sections:
  - title: Task definition
    line: 4
    size: 376
  - title: Rubric rationale
    line: 13
    size: 155
---

# TB-008: Nginx Rate Limiting Directive

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `nginx-request-logging`.
Original: configure Nginx with advanced logging and rate limiting in a container.
This tests knowledge of the specific Nginx directive name.

Canonical answer: `limit_req_zone` (defines the shared memory zone and rate).
Used in conjunction with `limit_req` in location blocks.

## Rubric rationale

- `content_contains_ci: [limit_req_zone]` — the single specific directive name.
- Tight `max_tokens: 64` enforces a direct answer.

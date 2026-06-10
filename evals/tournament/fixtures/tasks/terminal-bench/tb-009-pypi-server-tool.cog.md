---
type: workflow.variant
id: tb-009-pypi-server-tool
title: "TB-009: Local PyPI Server Tool Name"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, python, packaging]
terminal_bench_origin: pypi-server
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: create and host a Python package on a local PyPI server.
  This tests knowledge of the standard Python tool for hosting a local PyPI server.
case:
  prompt: |
    What is the name of the Python package/tool most commonly used to host a local PyPI-compatible package server? One word answer.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_any_of_ci: [pypiserver, devpi, pip2pi, twine]
  max_tokens: 64
sections:
  - title: Task definition
    line: 4
    size: 376
  - title: Rubric rationale
    line: 13
    size: 101
---

# TB-009: Local PyPI Server Tool Name

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `pypi-server`.
Original: create and host a Python package on a local PyPI server.
This tests knowledge of the standard local PyPI hosting tool.

Canonical answers: `pypiserver` (most common for this use case), `devpi` (enterprise alternative).
Either answer demonstrates CLI package hosting knowledge.

## Rubric rationale

- `content_contains_any_of_ci` checks for any canonical PyPI server tool name.

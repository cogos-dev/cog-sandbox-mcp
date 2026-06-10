---
type: workflow.variant
id: tb-013-pytorch-model-cli-entry
title: "TB-013: PyTorch MNIST Inference CLI — argparse"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, python, ml]
terminal_bench_origin: pytorch-model-cli
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: build a complete MNIST inference CLI tool with PyTorch.
  This tests knowledge of the standard Python CLI argument parsing module.
case:
  prompt: |
    What is the name of the Python standard library module used to add command-line argument parsing to a script (e.g. --model-path, --image)? One word answer.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [argparse]
  max_tokens: 64
sections:
  - title: Task definition
    line: 4
    size: 291
  - title: Rubric rationale
    line: 12
    size: 94
---

# TB-013: PyTorch Model CLI — argparse

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `pytorch-model-cli`.
Original: build MNIST inference CLI with PyTorch including argument parsing.
This tests knowledge of Python's CLI argument parsing module.

Canonical answer: `argparse` (Python standard library).

## Rubric rationale

- `content_contains_ci: [argparse]` — the single correct module name.

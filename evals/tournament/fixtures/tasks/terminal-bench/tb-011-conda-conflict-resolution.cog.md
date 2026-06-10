---
type: workflow.variant
id: tb-011-conda-conflict-resolution
title: "TB-011: Conda Dependency Conflict Resolution Approach"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, python, packaging]
terminal_bench_origin: conda-env-conflict-resolution
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: resolve conda environment dependency conflicts in a container.
  This tests knowledge of conda's conflict resolution subcommands.
case:
  prompt: |
    When conda reports a dependency conflict during environment creation, what conda subcommand and flag (or alternative tool) can show you the full dependency tree to diagnose the conflict? Give the conda command or tool name.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_any_of_ci: [conda info, conda search, mamba, pixi, conda tree, conda depends]
    content_contains_ci: [conda]
  max_tokens: 256
sections:
  - title: Task definition
    line: 4
    size: 474
  - title: Rubric rationale
    line: 15
    size: 268
---

# TB-011: Conda Dependency Conflict Resolution Approach

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `conda-env-conflict-resolution`.
Original: resolve conda environment dependency conflicts requiring specific package versions.
This tests knowledge of conda diagnostic commands.

Canonical approaches:
- `conda info package` or `conda search package` — shows available versions and deps
- `mamba` — faster solver with better conflict messages
- `conda env create --dry-run` — preview resolution

## Rubric rationale

- First `content_contains_any_of_ci` checks for a package manager name (conda/mamba/pixi).
- Second checks for a diagnostic operation keyword.
- Note: having two `content_contains_any_of_ci` in rubric means BOTH must match (each is independent).

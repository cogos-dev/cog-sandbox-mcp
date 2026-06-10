---
type: workflow.experiment
id: exp-002-terminal-bench
title: "Experiment 002: Terminal-Bench Knowledge Adaptation — CLI Knowledge vs Execution"
created: 2026-04-26
baseline_variant: sp-1-production
variants:
  system_prompt: [sp-1-production]
tasks:
  - tb-001-openssl-cert-command
  - tb-002-git-recovery-approach
  - tb-003-regex-log-pattern
  - tb-004-log-summary-command
  - tb-005-sqlite-recovery-approach
  - tb-006-jq-filter-approach
  - tb-007-git-leak-recovery
  - tb-008-nginx-rate-limit
  - tb-009-pypi-server-tool
  - tb-010-kv-store-grpc-proto
  - tb-011-conda-conflict-resolution
  - tb-012-query-optimize-explain
  - tb-013-pytorch-model-cli-entry
  - tb-014-qemu-alpine-ssh
  - tb-015-sanitize-git-secret
target: laptop-kernel
tags: [terminal-bench, experiment, knowledge, cli, public-benchmark-adaptation]
sections:
  - title: Hypothesis
    line: 4
    size: 676
  - title: Adaptation scope
    line: 15
    size: 560
  - title: Why only 15 tasks
    line: 24
    size: 788
  - title: Variant axes
    line: 39
    size: 237
  - title: Matrix expansion
    line: 45
    size: 204
  - title: Run configuration
    line: 51
    size: 446
  - title: Expected deliverables
    line: 59
    size: 329
  - title: Notes on bash gap
    line: 66
    size: 489
  - title: Judge identity
    line: 77
    size: 103
---

# Experiment 002: Terminal-Bench Knowledge Adaptation

## Hypothesis

Terminal-Bench 2.0 (89 tasks, all requiring bash execution in a sandboxed container) cannot be
run directly on the CogOS kernel's current tool surface — the kernel has no bash execution tool.
However, a knowledge-equivalent subset can be adapted: reformulating execution tasks as
"what command/approach would you use" questions, graded by content matching against canonical
CLI keywords. This tests the same underlying model knowledge without needing container execution.

The kernel-mediated small model (gemma4:e4b) may outperform claude-code on these structured
CLI knowledge questions due to the harness's tool-mediation reducing hallucination pressure.

## Adaptation scope

- **Original benchmark**: 89 tasks (Terminal-Bench 2.0), all requiring bash execution
- **Adapted subset**: 15 tasks (16.9%) where the task reduces to CLI knowledge retrieval
- **Unadaptable (74 tasks, 83.1%)**: require actual execution — build systems, ML training,
  container orchestration, binary analysis, cryptography operations. Bash execution tool needed.
- **Adaptation method**: Knowledge reformulation — reframe as "what command/approach" questions,
  grade by content_contains_ci rubrics against canonical answer keywords

## Why only 15 tasks

All 89 Terminal-Bench tasks execute in Docker containers with real filesystems, running processes,
and binary tools. The CogOS kernel's tool surface is information-retrieval only
(cog_search_memory, cog_read_cogdoc, cog_get_state, etc.) — no bash_exec tool exists.

Path (b) from the design spec: pick the subset where existing kernel tools can plausibly answer.
For Terminal-Bench, the best mapping is to LLM parametric knowledge (not kernel memory retrieval)
because TB tasks are about general CLI/systems knowledge, not CogOS-specific knowledge.

The 15 adapted tasks test:
- CLI command knowledge (openssl, git, grep/wc, sqlite, nginx)
- Framework tool knowledge (conda, jq, pypi, grpc, qemu)
- Security procedure knowledge (secrets removal, cert generation)

## Variant axes

No SP×TD cross-test in this experiment — task variation IS the experiment axis.
SP-1 (production) applied uniformly to all trials.
No TD variants needed: tasks are pure knowledge queries, no tool-description tuning.

## Matrix expansion

1 SP × 1 TD (baseline) × 15 tasks = 15 trials per target.
Three targets: laptop-kernel (gemma4:e4b), claude-sonnet, claude-haiku.
Total trials: 45 (15 per target, run separately).

## Run configuration

- Kernel target: laptop-kernel (Ollama gemma4:e4b via cog_dispatch_to_harness)
- Claude sonnet: kernel /v1/chat/completions → claude-code subprocess (Max OAuth)
- Claude haiku: kernel /v1/chat/completions → claude-code subprocess (Max OAuth)
- Sequential execution (Ollama single-thread constraint; ~7s × 15 = ~2min per kernel run)
- No judge-required tasks (all tasks are auto_gradable: true via content_contains_ci)

## Expected deliverables

1. `evals/runs/exp-002-terminal-bench_run_{ts}/results.jsonl` — 15 trial records per run
2. `evals/runs/exp-002-terminal-bench_run_{ts}/report.html` — dark-first 2-tab report
3. Per-cell pass-rate comparison: kernel vs sonnet vs haiku across 15 tasks
4. Adaptation cost notes for future benchmarks

## Notes on bash gap

The 74 unadaptable tasks require a bash_exec(command) tool in the harness.
Adding this tool is a SEPARATE, LARGER move requiring sandboxing.
NOT implemented in this experiment. Flagged for future work.

The meaningful public benchmark comparison will require either:
(a) Adding sandboxed bash execution to the kernel harness, OR
(b) Running TB directly via Harbor container registry with its own harness,
    then comparing results to this knowledge-query baseline.

## Judge identity

`cog://agents/identities/cog` — not used in this experiment (all auto-gradable).

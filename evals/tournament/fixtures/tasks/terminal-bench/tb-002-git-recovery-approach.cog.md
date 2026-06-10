---
type: workflow.variant
id: tb-002-git-recovery-approach
title: "TB-002: Git Lost-Changes Recovery Approach"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, git]
terminal_bench_origin: fix-git
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: find changes made before checkout to master and merge them back.
  This adaptation tests knowledge of git reflog and stash — the correct recovery primitives.
case:
  prompt: |
    I made changes on a git branch, then ran `git checkout master`, and now I cannot find my changes. Name the two git commands (or git subcommands) most useful for finding and recovering lost changes after a branch switch. One word each.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_any_of_ci: [reflog, stash]
    content_contains_ci: [git]
  max_tokens: 128
sections:
  - title: Task definition
    line: 4
    size: 412
  - title: Rubric rationale
    line: 13
    size: 230
---

# TB-002: Git Lost-Changes Recovery Approach

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `fix-git`.
Original: recover changes that were checked in before a branch switch.
This adaptation tests knowledge of git primitives for lost-change recovery.

Canonical answers: `git reflog` (shows all HEAD movements, including before the checkout)
and `git stash list` (if changes were stashed). Either appearing confirms CLI knowledge.

## Rubric rationale

- `content_contains_any_of_ci: [reflog, stash]` — either correct primitive must appear.
- `content_contains_ci: [git]` — confirms the answer is in git namespace.
- No `expected_tools` — pure knowledge.

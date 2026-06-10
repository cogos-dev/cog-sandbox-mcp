---
type: workflow.variant
id: tb-007-git-leak-recovery
title: "TB-007: Git Secret Removal from History"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, git, security]
terminal_bench_origin: git-leak-recovery
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: extract and remove accidentally committed secrets from git history.
  This tests knowledge of the two canonical git history-rewriting tools.
case:
  prompt: |
    Name the two most commonly used tools for permanently removing a file or secret from all commits in a git repository's history (not just the latest commit). One tool name per line.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_any_of_ci: [bfg, filter-branch, filter-repo, git-filter-repo]
  max_tokens: 128
sections:
  - title: Task definition
    line: 4
    size: 393
  - title: Rubric rationale
    line: 13
    size: 168
---

# TB-007: Git Secret Removal from History

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `git-leak-recovery`.
Original: extract and remove accidentally committed API keys/secrets from git history.
This tests knowledge of git history-rewriting tools.

Canonical answers: `git filter-repo` (modern, recommended) or `BFG Repo Cleaner` (legacy).
Legacy: `git filter-branch` (slow, deprecated for this use case).

## Rubric rationale

- `content_contains_any_of_ci` checks for any of the canonical tools.
- Any mention of bfg, filter-branch, or filter-repo confirms CLI knowledge.

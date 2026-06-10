---
type: workflow.variant
id: tb-015-sanitize-git-secret
title: "TB-015: Git Sanitization — Remove Credentials"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, git, security]
terminal_bench_origin: sanitize-git-repo
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: remove API keys and credentials from git repository history.
  This tests knowledge of the standard approach: git history rewriting + .gitignore update.
case:
  prompt: |
    After removing a file containing secrets from git history, what two steps are required to prevent the secret from re-entering: (1) what file do you update, and (2) what do you tell collaborators to do with their local clones?
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [gitignore]
    content_contains_any_of_ci: [re-clone, reclone, fresh clone, force push, force-push]
  max_tokens: 256
sections:
  - title: Task definition
    line: 4
    size: 413
  - title: Rubric rationale
    line: 14
    size: 309
---

# TB-015: Git Sanitization — Remove Credentials

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `sanitize-git-repo`.
Original: remove API keys and credentials from a git repository's history.
This tests knowledge of the two mandatory post-history-rewrite steps.

Canonical answers:
1. Update `.gitignore` to prevent secret files from being tracked again.
2. Tell collaborators to re-clone (not pull/fetch) since history was rewritten.

## Rubric rationale

- First `content_contains_any_of_ci` checks for .gitignore.
- Second checks for the re-clone instruction.
- Note: having two `content_contains_any_of_ci` in the YAML frontmatter — only the LAST one
  will be read by yaml.safe_load (duplicate keys). Consolidating into one check below.

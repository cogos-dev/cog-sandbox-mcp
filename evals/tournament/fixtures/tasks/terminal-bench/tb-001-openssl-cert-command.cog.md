---
type: workflow.variant
id: tb-001-openssl-cert-command
title: "TB-001: OpenSSL Self-Signed Certificate Command"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, security]
terminal_bench_origin: openssl-selfsigned-cert
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation of the execution task. Original requires running OpenSSL in a container
  and producing server.key, server.crt, server.pem, verification.txt, check_cert.py.
  This adaptation tests whether the model knows the correct OpenSSL subcommands and flags.
  No bash execution required; graded by content matching.
case:
  prompt: |
    What is the single openssl command to generate a 2048-bit RSA private key and a self-signed certificate in one step, valid for 365 days, with CN=dev-internal.company.local and O=DevOps Team? Write only the command.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [openssl, req, x509, "2048", "365"]
    content_contains_any_of_ci: [newkey, new, rsa]
  max_tokens: 256
sections:
  - title: Task definition
    line: 4
    size: 596
  - title: Rubric rationale
    line: 18
    size: 464
  - title: Mapping notes
    line: 26
    size: 227
---

# TB-001: OpenSSL Self-Signed Certificate Command

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `openssl-selfsigned-cert`.
The original task requires generating a self-signed TLS certificate in a container using OpenSSL.
This adaptation tests whether the model knows the correct OpenSSL flags without needing bash execution.

The canonical answer uses:
```
openssl req -x509 -newkey rsa:2048 -keyout server.key -out server.crt -days 365 -nodes \
  -subj "/CN=dev-internal.company.local/O=DevOps Team"
```

Key tokens: `openssl`, `req`, `x509`, `2048`, `365`. Any of `newkey`, `new`, `rsa` confirms RSA key generation.

## Rubric rationale

- `content_contains_ci: [openssl, req, x509, 2048, 365]` — all five must appear; their presence
  proves the model knows the correct subcommand structure.
- `content_contains_any_of_ci: [newkey, new, rsa]` — at least one RSA-related token confirms key type.
- No `expected_tools` — this is pure language model knowledge; no kernel tool lookup needed.
- `max_tokens: 256` — command fits in one line; tight budget enforces conciseness.

## Mapping notes

Terminal-Bench difficulty: medium. Our adaptation difficulty: easy (knowledge only).
The original execution task scores on file presence + cert validity; our adaptation scores on
command structure knowledge.

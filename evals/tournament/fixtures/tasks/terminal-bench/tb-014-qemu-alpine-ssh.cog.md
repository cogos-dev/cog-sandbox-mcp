---
type: workflow.variant
id: tb-014-qemu-alpine-ssh
title: "TB-014: QEMU Port Forwarding for SSH"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, virtualization, networking]
terminal_bench_origin: qemu-alpine-ssh
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: boot Alpine Linux in QEMU with SSH access using port forwarding.
  This tests knowledge of the QEMU flag used to forward host ports to guest ports.
case:
  prompt: |
    What QEMU command-line flag is used to set up user-mode network with port forwarding (e.g. to forward host port 2222 to guest port 22 for SSH)? Just the flag name.
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [netdev]
    content_contains_any_of_ci: [hostfwd, "-net user", -nic]
  max_tokens: 128
sections:
  - title: Task definition
    line: 4
    size: 384
  - title: Rubric rationale
    line: 16
    size: 158
---

# TB-014: QEMU Port Forwarding for SSH

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `qemu-alpine-ssh`.
Original: boot Alpine Linux in QEMU with SSH access via port forwarding.
This tests knowledge of QEMU's port forwarding mechanism.

Canonical approach:
```
-netdev user,id=net0,hostfwd=tcp::2222-:22 -device virtio-net-pci,netdev=net0
```
Or the older form: `-net user,hostfwd=tcp::2222-:22`

## Rubric rationale

- `content_contains_ci: [netdev]` — the modern netdev flag.
- `content_contains_any_of_ci` checks for hostfwd or equivalent patterns.

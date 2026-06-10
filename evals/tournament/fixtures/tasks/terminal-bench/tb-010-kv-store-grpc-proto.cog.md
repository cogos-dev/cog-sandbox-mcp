---
type: workflow.variant
id: tb-010-kv-store-grpc-proto
title: "TB-010: gRPC Key-Value Service Definition"
created: 2026-04-26
variant_class: task
auto_gradable: true
tags: [terminal-bench, task, knowledge, cli, grpc, networking]
terminal_bench_origin: kv-store-grpc
terminal_bench_version: "2.0"
adaptation_note: >
  Knowledge reformulation. Original: build a key-value store server using gRPC protocol.
  This tests knowledge of the protobuf file extension and gRPC service definition syntax.
case:
  prompt: |
    In gRPC, what file extension is used for protocol buffer service definition files, and what keyword defines a service in those files? Format: "extension: keyword".
  rubric:
    expected_tools: []
    forbidden_tools: []
    content_contains_ci: [proto, service]
  max_tokens: 64
sections:
  - title: Task definition
    line: 4
    size: 298
  - title: Rubric rationale
    line: 12
    size: 118
---

# TB-010: gRPC Key-Value Service Definition

## Task definition

Knowledge-equivalent reformulation of Terminal-Bench `kv-store-grpc`.
Original: build a key-value store server using gRPC protocol with full implementation.
This tests knowledge of protobuf/gRPC definition file syntax.

Canonical answer: `.proto` extension, `service` keyword.

## Rubric rationale

- `content_contains_ci: [proto, service]` — both must appear confirming basic gRPC knowledge.

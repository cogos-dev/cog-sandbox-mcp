---
type: workflow.variant
id: sp-1-production
title: "SP-1: Production Dispatch Prompt (Baseline)"
created: 2026-04-25
variant_class: system-prompt
baseline_of: null
ablation: null
tags: [tournament, system-prompt]
sections:
  - title: Variant content
    line: 4
    size: 559
  - title: Hypothesis tested
    line: 16
    size: 240
  - title: Source / origin
    line: 20
    size: 159
---

# SP-1: Production Dispatch Prompt (Baseline)

## Variant content

You are the resident local CogOS harness.
Stay local-only. Use only the provided kernel tools. Be concise and finish with a direct answer.

CogDoc URIs use the form cog://<type>/<path>. Valid types:
  mem, adr, role, skill, agent, spec, status, ledger, crystal,
  kernel, canonical, config, ontology, work, handoff, artifact, docs, hooks
Example: cog://adr/077 (ADRs resolve by numeric prefix).
If cog_search_memory returns ".cog/.state/buses/.../events.jsonl#N", that's a chat log entry,
not a readable CogDoc — do not try to read it.

## Hypothesis tested

Known-working baseline. All other SP variants are measured as deltas against this one. Establishes the floor for the experiment and validates that the eval harness itself is functional before any ablation is applied.

## Source / origin

Exact text of `localHarnessDispatchPrompt` from `internal/engine/local_agent_harness.go` (myrgic/cogos) lines 59-67. Captured 2026-04-25.

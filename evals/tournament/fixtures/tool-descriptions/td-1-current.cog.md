---
type: workflow.variant
id: td-1-current
title: "TD-1: Current Tool Descriptions (Baseline)"
created: 2026-04-25
variant_class: tool-description
baseline_of: null
ablation: null
tags: [tournament, tool-description]
overrides:
  cog_search_memory: "Search the CogDoc memory corpus. Returns ranked results."
  cog_read_cogdoc: "Read a CogDoc by URI. Returns content with parsed frontmatter and schema hints."
  cog_query_field: "Query the attentional field. Returns top-N items by salience."
  cog_check_coherence: "Run workspace coherence validation"
  cog_get_state: "Get the continuous process state — uptime, field size, stats"
  cog_dispatch_to_harness: "Dispatch a task to the local agent harness"
  cog_emit_event: "Emit a custom event to the workspace ledger"
sections:
  - title: Variant content
    line: 4
    size: 1001
  - title: Hypothesis tested
    line: 18
    size: 269
  - title: Source / origin
    line: 22
    size: 156
---

# TD-1: Current Tool Descriptions (Baseline)

## Variant content

Override map — exact current 1-line descriptions from `tool_loop.go` lines 60-200 for the 7 orchestration tools:

- `cog_search_memory`: "Search the CogDoc memory corpus. Returns ranked results."
- `cog_read_cogdoc`: "Read a CogDoc by URI. Returns content with parsed frontmatter and schema hints."
- `cog_query_field`: "Query the attentional field. Returns top-N items by salience."
- `cog_check_coherence`: "Run workspace coherence validation"
- `cog_get_state`: "Get the continuous process state — uptime, field size, stats"
- `cog_dispatch_to_harness`: "Dispatch a task to the local agent harness"
- `cog_emit_event`: "Emit a custom event to the workspace ledger"

Note: `cog_dispatch_to_harness` and `cog_emit_event` descriptions were inferred from the tool_loop.go pattern for tools not in lines 60-200 verbatim. The 5 explicitly listed tools (cog_search_memory, cog_read_cogdoc, cog_query_field, cog_check_coherence, cog_get_state) use verbatim text from tool_loop.go.

## Hypothesis tested

Baseline for all TD variants. Establishes current tool-description quality as the floor. The question all other TD variants answer is: does adding use-cases, anti-patterns, or stripping to minimal descriptions meaningfully change model behavior?

## Source / origin

Verbatim descriptions from `/Users/slowbro/workspaces/cogos-dev/cogos/internal/engine/tool_loop.go` lines 60-200. Captured 2026-04-25.

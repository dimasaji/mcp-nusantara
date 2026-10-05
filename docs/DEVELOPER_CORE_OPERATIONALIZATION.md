# Nusantara Developer Core Operationalization

## Purpose

Operational layer for Developer Core V1.

This layer orchestrates engineering analysis without automatically modifying
production source code.

## Pipeline

inspect
→ graph
→ impact
→ evidence
→ gap
→ root_cause
→ proposal
→ experiment
→ evaluation
→ release_check

## Safety Contract

- Production write: disabled
- Shell execution: disabled
- Automatic patch: disabled
- Approval: required
- Existing tools: preserved
- Gate 14 regression: required
- Gate 15 regression: required
- Gate 16 regression: required
- Gate 17 regression: required

## Principle

Developer Core must produce evidence and a deterministic engineering plan
before a controlled change can be considered.

The operationalization layer does not replace the existing Gate 14–17 engines.
It coordinates them.

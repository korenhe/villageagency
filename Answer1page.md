# Agent Village Backend (Architecture Summary)

## Overview

This project implements a backend where AI agents behave as **stateful social entities** with both private and public presence.

The core design principle is:

> Agent behavior is controlled by **context and trust boundaries**, not hardcoded logic.

---

## What I Built

I built a minimal system centered around a **unified LLM interface**:

chat(agent_id, user_type, message, mode)

This allows agent behavior to emerge from:

- identity (name, bio)
- trust context (owner vs stranger vs public)
- recent state (memory, diary)

Key components:

- **Private Memory (`living_memory`)**
  - owner-only, LLM-filtered, enables personalization

- **Public Diary (`living_diary`)**
  - shared feed, repetition-aware, no private leakage

- **Proactive Scheduler**
  - agents act autonomously (not request-driven)
  - triggered by probability + recent interaction

> The system minimizes explicit logic and instead shapes behavior through structured context.

---

## Trust Boundaries

The system enforces three contexts:

- **Owner**: full access to private memory → personalized responses
- **Stranger**: no memory access → safe, generic responses
- **Public Feed**: constrained generation → no private details

Enforcement happens at two levels:

1. **Data-level isolation** (memory only loaded for owner)
2. **Prompt-level constraints** (explicit rules per context)

> Sensitive data is never exposed to the model in restricted contexts.

---

## Scaling Considerations

The system is primarily **LLM-bound**, not database-bound.

Key risks and mitigations:

- **LLM throughput**
  - queue + rate limiting + minimal context injection

- **Scheduler scaling**
  - move to distributed workers + agent sharding
  - pretty easy since the database is already on cloud

- **Feed access**
  - pagination + indexing (`created_at`) to reduce the UI time

- **Memory growth**
  - summarization(squash) + importance filtering

> Scaling requires controlling how often agents think, not just storing more data.

---

## Observability

Since behavior is LLM-driven, observability focuses on **decision transparency**:

- **Structured logs**
  - messages, diary generation, trigger reasons

- **Per-agent timeline (`living_log`)**
  - reconstruct behavior for debugging

- **Behavior signals**
  - activity frequency, latency, memory growth

Future extensions:
- metrics (e.g., Prometheus)
- dashboards and alerting

---

## Schema Design

The schema enforces separation of concerns:

| Table | Purpose |
|------|--------|
| living_agents | identity |
| living_memory | private data |
| living_diary | public feed |
| living_log | behavior trace |

Key properties:

- **strict private/public separation**
- **append-only design** for traceability
- **LLM-oriented access (top-k, recent context)**

Optional extension:
- **Row Level Security (RLS)** to enforce access control at the database layer

---

## Summary

Agents behave as:

- private companions (memory)
- public actors (feed)
- autonomous entities (scheduler)

> Behavior emerges from controlled context and enforced trust boundaries.

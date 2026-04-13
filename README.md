# Agent Village Backend

## Overview

This project implements the backend for a system where AI agents behave as **persistent social entities** — each with identity, memory, and the ability to act both privately and publicly.

The system is designed around a core idea:

> Agents operate under different **trust boundaries**, and their behavior must adapt accordingly.

---

## What I Built

I built a minimal backend system where agents behave as **stateful, context-aware entities** with both private and public presence.

The system is centered around a **unified LLM interface**, with behavior controlled by context rather than hardcoded logic.

---

### 1. Unified Agent Interface

All agent behavior is routed through:

chat(agent_id, user_type, message, mode)

This design ensures:
- consistent prompt construction
- clear separation of concerns (identity, memory, behavior)
- easy extensibility (new modes or behaviors)

---

### 2. Context-Driven Behavior

Agent behavior is not hardcoded, but emerges from:

- identity (name, bio)
- trust context (owner vs stranger vs public)
- recent state (memory, diary)

This allows the same agent to:
- act as a personal companion
- interact safely with strangers
- produce public content

---

### 3. Private Memory System

- Owner-specific data is stored in `living_memory`
- Memory is extracted using LLM judgment (importance-based)
- Only injected in owner context

This enables long-term personalization without leaking data.

---

### 4. Public Diary System

- Agents generate diary entries into a shared feed
- Recent entries are injected to reduce repetition
- Output is constrained to avoid private leakage

---

### 5. Proactive Behavior Engine

Agents are not request-driven.
A background scheduler allows them to act autonomously.

Behavior is triggered by:
- probabilistic signals
- recent interaction with owner

This makes agents feel persistent and active rather than reactive.

---

### Design Insight

> The system minimizes explicit logic and instead controls behavior through structured context and constraints.

---


## Trust Boundaries

The system enforces three trust contexts: **owner**, **stranger**, and **public feed**.
The key design principle is that **data access is restricted before generation**, not filtered after.

---

### 1. Owner (Full Trust)

- The agent can access:
  - private memory (`living_memory`)
  - past interactions
- The agent can store new personal information via memory extraction
- Responses are personalized and context-aware

---

### 2. Stranger (Limited Trust)

- The agent **does not load any private memory**
- The prompt explicitly enforces:
  - no personal data disclosure
  - general, non-specific responses

This ensures that even if sensitive data exists, it is never exposed to the model in this context.

---

### 3. Public Feed (Broadcast)

- Diary entries are generated under strict constraints:
  - no private details
  - abstract or generalized reflections
- Only public-safe data is used (no memory injection)

---

### Enforcement Strategy

Trust boundaries are enforced at two levels:

1. **Data-level isolation**
   - `living_memory` is only queried for owner interactions
   - diary generation does not access private memory

2. **Prompt-level constraints**
   - explicit instructions prevent leakage
   - different prompts per trust context

---

### Design Insight

> Preventing access is safer than filtering output.
> The model cannot leak what it never sees.

---

## Scaling Considerations

If the system scales to ~1,000 agents, the primary bottleneck is **LLM inference**, not storage or networking.

### 1. LLM Inference Throughput (Primary Bottleneck)

Each agent action (chat or diary) triggers an LLM call. With 1,000 agents acting periodically, this quickly becomes the dominant cost and latency constraint.

Mitigations:
- Introduce an **inference queue** to serialize or batch requests
- Apply **per-agent rate limiting** (e.g., max actions per hour)
- Reduce prompt size by only injecting **relevant context (recent memory / recent diary)**

---

### 2. Scheduler Scalability

The current scheduler is a single in-process loop. At scale, this becomes:

- a coordination bottleneck
- a single point of failure

Mitigations:
- Move to **distributed workers**
- Partition agents into shards (e.g., by agent_id hash)
- Use a lightweight job queue (e.g., Redis-based)

---

### 3. Feed Access Pattern

While Supabase handles storage, the backend must still define **how data is accessed efficiently**.

As the number of diary entries grows:

- returning the entire feed becomes inefficient
- clients need partial views of the data
- currently I use a global config: AGENT_MEMORY_MAX to restrict the max memory retrieved, and use desc order date + limit to reduce the size. (just in chat, not UI)

Mitigations:
- use **pagination (limit + offset / cursor)**
- index by `created_at` for fast retrieval
- only fetch recent entries for UI

---

### Clarification

Supabase provides storage and querying, but **access patterns (pagination, filtering, ordering)** must still be designed at the application level.

---

### 4. Memory Growth

Unbounded memory storage leads to:
- increased prompt size
- higher inference cost

Mitigations:
- Periodic **memory summarization**
- Store only **high-signal memories** (LLM-filtered)

---

### Key Insight

> The system is LLM-bound, not database-bound.
> Scaling requires controlling *when and how often agents think*, not just how data is stored.

---

## Agent Observability

Understanding agent behavior is critical, since most logic is LLM-driven and non-deterministic.

### 1. Structured Logging

All key actions are logged:

- user → agent messages
- agent replies
- diary generation
- trigger reasons (e.g., random, recent interaction)

This allows tracing **why an agent acted**, not just what it did.

---

### 2. Activity Timeline (Per-Agent)

Using `living_log`, each agent’s behavior can be reconstructed as a timeline:

- conversations
- diary writes
- memory extraction events

This is essential for:
- debugging unexpected outputs
- explaining agent decisions

---

### 3. Behavior Signals

We can derive signals such as:

- diary frequency
- response latency
- memory growth rate

These help detect:
- runaway agents (too active)
- repetitive outputs
- degraded behavior quality

---

### 4. Debugging Strategy

Instead of treating LLM output as opaque, the system exposes:

- prompt inputs (instruction composition)
- trigger conditions
- recent context (memory / diary)

This makes LLM behavior **inspectable and debuggable**, not a black box.

---

### 5. Future Observability Improvements

In a production system, I would extend observability with:

- **metrics collection (e.g., Prometheus)**
  - LLM latency
  - request volume
  - agent activity frequency

- **dashboards (e.g., Grafana)**
  - agent behavior trends
  - anomaly detection

- **alerting**
  - unusually high activity (cost risk)
  - repeated failures

---

### Design Choice

For this prototype, I focused on **structured logging and traceability**,
which provides sufficient visibility without adding operational complexity.


### Key Insight

> Observability focuses on *decision visibility* —
> making it clear why an agent acted, not just what it produced.

---

## Schema Design Rationale

The schema is designed to enforce **trust boundaries at the data level**, not just via prompts.

### Separation of Concerns

| Table | Role |
|------|------|
| `living_agents` | identity (public) |
| `living_memory` | private owner data |
| `living_diary` | public feed |
| `living_log` | behavior trace |

---

### 1. Private vs Public Data Isolation

- `living_memory` is **never used** in stranger or public contexts
- `living_diary` is always treated as **public-safe output**

This prevents accidental leakage by design.

---

### 2. Append-Only Behavior

Most tables (diary, log, memory) are append-only:

- simplifies reasoning
- preserves history
- enables replay/debugging

---

### 3. LLM-Oriented Data Access

Data access patterns are optimized for LLM usage:

- recent memory only (top-k)
- recent diary only (for de-duplication)
- minimal context injection

---

### 4. Data Access Control (Optional Extension)

In a production setting, trust boundaries can be further enforced at the database level using **Row Level Security (RLS)** in Supabase.

For example:

- `living_memory`
  - only accessible by the agent’s owner
- `living_diary`
  - publicly readable
- `living_agents`
  - public identity data

This ensures that even if the backend logic fails,
**unauthorized data access is still prevented at the database layer**.

---

### Design Trade-off

For this prototype, I handled trust boundaries at the application layer for simplicity,
but the schema is compatible with adding RLS policies.


### 4. Trade-offs

- No strict schema for “importance” → handled by LLM
- No cross-agent shared memory → avoids leakage risk
- No heavy normalization → favors simplicity and speed

---

### Key Insight

> The schema is designed to minimize **data leakage risk** and
> maximize **clarity of agent context**, rather than perfect normalization.

---

## Summary

Agents behave as:

- private companions
- public actors
- autonomous entities

> behavior emerges from controlled context + trust boundaries

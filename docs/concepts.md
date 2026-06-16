# Concepts

A short mental model of what Tessera stores and how the SDK surfaces it. You don't need this to
use the SDK, but it explains why the methods are shaped the way they are.

## Turns, episodes, and facts

You write **turns** (`memories.add`) — one message each, with a `role` and `content`.
Consolidation then derives longer-lived structures from them:

- **Episodes** (`ep_` ids) — durable records of something that happened. Searchable and pinnable.
- **Facts** (`ft_` ids) — extracted statements (subject–relation–object) with a confidence and a
  validity time. Correctable.

The id prefix tells you which kind of item you're holding, and which operations apply:
`correct` works on `ft_` ids; `pin`/`unpin` work on `ep_` ids.

## Consolidation

By default `memories.add` is asynchronous: the turn is stored immediately and a background job
extracts facts and episodes from it. The response carries the `turn_id` and, when relevant, a
`job` handle you can poll with `jobs.get`.

Pass `mode="sync"` to consolidate inline and get a `ConsolidationSummary` (counts of what was
created) in the same call. Pass `infer=False` to store the turn raw with no consolidation at all —
useful for notes and conventions you don't want re-interpreted.

## Bi-temporal facts

Facts track two timelines: when something was true in the world (`t_valid`) and what the system
believed over time. `correct` revises a fact's object while preserving this history, and `search`/
`query` accept `as_of` (world time) and `known_as_of` (belief time) to ask "what did we know then?"

## Procedures and resources

Beyond conversational memory, Tessera stores two other kinds of recallable knowledge:

- **Procedures** (`client.procedures`) — reusable how-tos: a `trigger` (the situation), `steps`
  (what to do), and `success` (the good outcome). Recalled by similarity to a task, and reinforced
  by recording outcomes.
- **Resources** (`client.resources`) — blob handles (e.g. images) with a caption, recalled by
  caption or visual content.

See [Procedures and resources](guides/procedures-and-resources.md).

## Search vs query

- **`search`** returns ranked, typed hits and never calls an LLM — cheap and deterministic.
- **`query`** composes those hits into an answer-shaped `context` string (plus structured
  `facts`/`episodes`/`foresight`), and may call an LLM server-side.

Use `search` when you want to rank or filter results yourself; use `query` when you want context
to hand to a model.

## Scope: user_id and session_id

Every memory belongs to a partition identified by `user_id` and/or `session_id`. These are labels,
not authentication — the API key is the tenant boundary. Conventionally `user_id` is the durable
owner (a person, or `repo:<name>` for a codebase) and `session_id` is an optional task/session
sub-scope. The server requires at least one of the pair on most calls.

# Beads PRD

**Bead:** bd-2d8  
**Created:** 2026-02-21  
**Status:** Draft

## Bead Metadata

```yaml
depends_on: []
parallel: true
conflicts_with: []
blocks: []
estimated_hours: 3
```

---

## Problem Statement

### What problem are we solving?

Billing analysis currently has no single structured log record that ties request input, response output, cache signals (`cache_write`, `cache_hit` when present), and the authenticated user identity to one request. This makes BILLING_MODEL charge debugging slow and error-prone, especially when reconciling token usage and cache behavior across OpenAI and Anthropic compatible routes.

### Why now?

Cost attribution and charging analysis need faster observability now. Without this, support/debug cycles require manual correlation across multiple logs and payload files, increasing time-to-diagnosis and risk of incorrect billing analysis.

### Who is affected?

- **Primary users:** Gateway operators maintaining BILLING_MODEL charging accuracy.
- **Secondary users:** Teams investigating billing disputes or anomalous charge patterns.

---

## Scope

### In-Scope

- Add structured application logs for both `/v1/chat/completions` and `/v1/messages` flows.
- Include request-side input summary needed for billing analysis.
- Include response-side output summary needed for billing analysis.
- Include `cache_write` and `cache_hit` in logs only when present in parsed response payload.
- Include request user identity context (username when available; otherwise fallback identifier) alongside billing user id.
- Cover both streaming and non-streaming paths.
- Add/extend tests to validate presence/absence behavior and route parity.

### Out-of-Scope

- Changing BILLING_MODEL pricing rules, charge formula, or deduction behavior.
- Altering external API response payload shape returned to clients.
- Adding new authentication providers or changing API-key verification logic.
- Building dashboards or storage pipelines outside existing gateway logging.

---

## Proposed Solution

### Overview

Add a route-level structured billing-observability log event in both OpenAI and Anthropic handlers after parsed payload data is available. The event records input/output billing fields, optional cache fields, and request identity context derived from `request.state.auth_context` plus available user metadata. The implementation keeps gateway transparency by logging only and does not mutate user request content or charging semantics.

### User Flow (operator)

1. User sends request through OpenAI or Anthropic compatible endpoint.
2. Gateway processes request/response and billing as usual.
3. Operator can inspect one structured log entry per request to correlate user identity, token/usage fields, and cache behavior for billing analysis.

---

## Requirements

### Functional Requirements

#### Structured Billing Observability Log

The gateway must emit one structured app log entry per request (both APIs) with billing analysis fields from input and output.

**Scenarios:**

- **WHEN** a valid OpenAI request completes (streaming or non-streaming) **THEN** the gateway logs request summary, output summary, and user identity context in a consistent structure.
- **WHEN** a valid Anthropic request completes (streaming or non-streaming) **THEN** the gateway logs the same structure with API-specific response mapping handled internally.

#### Optional Cache Field Logging

The gateway must include cache fields only if present in the parsed response payload.

**Scenarios:**

- **WHEN** response payload includes `cache_hit` and/or `cache_write` **THEN** log entry includes those keys and values.
- **WHEN** response payload does not include these fields **THEN** log entry omits them (no synthetic defaults that imply cache usage).

#### User Identity Context

The gateway must include a user identity field suitable for billing analysis correlation.

**Scenarios:**

- **WHEN** authenticated context includes username metadata **THEN** log entry includes that username.
- **WHEN** username is unavailable (for example env-key mode) **THEN** log entry includes fallback identity (`user_id` or explicit null-safe marker) without breaking request handling.

### Non-Functional Requirements

- **Performance:** Logging must not add blocking I/O beyond existing logger usage; no additional external network calls.
- **Security:** Do not log secrets (raw API keys/tokens); only billing-safe identity fields.
- **Accessibility:** Not applicable (server-side change).
- **Compatibility:** Preserve existing OpenAI/Anthropic API behavior and billing deductions.

---

## Success Criteria

- [ ] OpenAI route emits structured billing-observability log containing input/output fields and identity context for both streaming and non-streaming responses.
  - Verify: `pytest tests/unit/test_routes_openai.py -v`
- [ ] Anthropic route emits equivalent structured billing-observability log with optional cache fields when present.
  - Verify: `pytest tests/unit/test_routes_anthropic.py -v`
- [ ] Optional `cache_hit`/`cache_write` keys are logged only when present in parsed payload.
  - Verify: `pytest tests/unit/test_routes_openai.py -k "cache_hit or cache_write" -v`
- [ ] Existing debug logger behavior remains intact (no regression in middleware/logger unit tests).
  - Verify: `pytest tests/unit/test_debug_logger.py tests/unit/test_debug_middleware.py -v`

---

## Technical Context

### Existing Patterns

- Pattern 1: `kiro/routes_openai.py` uses `request.state.auth_context` and `billing_user_id` before billing checks and usage deduction.
- Pattern 2: `kiro/routes_anthropic.py` mirrors OpenAI billing/auth-context flow for parity.
- Pattern 3: `kiro/debug_middleware.py` captures incoming request body only; route layer handles richer business-context logging.
- Pattern 4: `kiro/debug_logger.py` already provides request/kiro payload buffering and flush/discard lifecycle; route code can add structured app logs without changing API outputs.

### Key Files

- `kiro/routes_openai.py` - OpenAI request handling, streaming/non-streaming usage parsing, billing deduction points.
- `kiro/routes_anthropic.py` - Anthropic request handling with analogous billing and response parsing flow.
- `kiro/debug_logger.py` - Existing debug logging lifecycle and file-based buffers.
- `kiro/debug_middleware.py` - Entry-point request body capture for target endpoints.
- `tests/unit/test_routes_openai.py` - Route-level behavior tests to extend for logging assertions.
- `tests/unit/test_routes_anthropic.py` - Route-level parity tests to extend for logging assertions.
- `tests/unit/test_debug_logger.py` - Regression safety for debug logger behavior.
- `tests/unit/test_debug_middleware.py` - Regression safety for middleware logging behavior.

### Affected Files

Files this bead will modify (for conflict detection):

```yaml
files:
  - kiro/routes_openai.py # add structured billing-observability logging for input/output/cache fields + identity
  - kiro/routes_anthropic.py # add equivalent logging for anthropic path
  - tests/unit/test_routes_openai.py # validate log payload shape and optional cache fields
  - tests/unit/test_routes_anthropic.py # validate log payload shape and optional cache fields
```

---

## Open Questions

| Question                                                                                                               | Owner       | Due Date     | Status |
| ---------------------------------------------------------------------------------------------------------------------- | ----------- | ------------ | ------ |
| In env API-key mode where `user_id` is null, should identity field be explicit `"anonymous_env_key"` or null + source? | Implementer | During /ship | Open   |
| Should `cache_hit`/`cache_write` be logged from final response only, or also intermediate streaming chunks if seen?    | Implementer | During /ship | Open   |

---

## Tasks

### Define billing observability log schema [design]

A shared structured log schema is documented and used by both API routes for billing analysis fields, identity context, and optional cache metadata.

**Metadata:**

```yaml
depends_on: []
parallel: false
conflicts_with: []
files:
  - kiro/routes_openai.py
  - kiro/routes_anthropic.py
```

**Verification:**

- `pytest tests/unit/test_routes_openai.py -v`
- `pytest tests/unit/test_routes_anthropic.py -v`

### Add OpenAI structured logging for input/output/cache fields [implementation]

OpenAI handler logs request input/output billing context with optional `cache_hit`/`cache_write` and identity context across streaming and non-streaming paths.

**Metadata:**

```yaml
depends_on:
  - Define billing observability log schema
parallel: false
conflicts_with:
  - Add Anthropic structured logging for input/output/cache fields
files:
  - kiro/routes_openai.py
  - tests/unit/test_routes_openai.py
```

**Verification:**

- `pytest tests/unit/test_routes_openai.py -v`

### Add Anthropic structured logging for input/output/cache fields [implementation]

Anthropic handler logs equivalent billing context and optional cache metadata with the same schema guarantees as OpenAI.

**Metadata:**

```yaml
depends_on:
  - Define billing observability log schema
parallel: false
conflicts_with:
  - Add OpenAI structured logging for input/output/cache fields
files:
  - kiro/routes_anthropic.py
  - tests/unit/test_routes_anthropic.py
```

**Verification:**

- `pytest tests/unit/test_routes_anthropic.py -v`

### Add parity and optional-field regression tests [test]

Unit tests enforce route parity and confirm optional cache fields are logged only when present while preserving existing behavior.

**Metadata:**

```yaml
depends_on:
  - Add OpenAI structured logging for input/output/cache fields
  - Add Anthropic structured logging for input/output/cache fields
parallel: false
conflicts_with: []
files:
  - tests/unit/test_routes_openai.py
  - tests/unit/test_routes_anthropic.py
  - tests/unit/test_debug_logger.py
  - tests/unit/test_debug_middleware.py
```

**Verification:**

- `pytest tests/unit/test_routes_openai.py tests/unit/test_routes_anthropic.py -v`
- `pytest tests/unit/test_debug_logger.py tests/unit/test_debug_middleware.py -v`

---

## Notes

- This PRD is specification-only for `/create`; no implementation changes are included.
- Scope confirms both API surfaces (`/v1/chat/completions` and `/v1/messages`) as requested.

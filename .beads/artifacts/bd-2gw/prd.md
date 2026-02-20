# Beads PRD

**Bead:** bd-2gw  
**Created:** 2026-02-20  
**Status:** Draft

## Bead Metadata

```yaml
depends_on: []
parallel: true
conflicts_with: []
blocks: []
estimated_hours: 1
```

---

## Problem Statement

### What problem are we solving?

Root-level documentation and localized docs still use the old "Kiro Gateway" branding, and a docs attribution line to `@jwadow` needs to be removed. This creates inconsistent product naming and unwanted attribution text in published documentation.

### Why now?

The project has moved to TrollLLM branding and docs should reflect current identity before further documentation updates. Delaying this creates churn and repeated cleanup in future docs work.

### Who is affected?

- **Primary users:** Maintainers and users reading repository docs.
- **Secondary users:** Translators and contributors updating localized documentation.

---

## Scope

### In-Scope

- Replace user-facing "Kiro Gateway" branding with "TrollLLM" in root/docs markdown documentation.
- Remove the attribution line in docs/README that credits `@jwadow`.
- Apply the same branding replacement to localized docs in `docs/*` where the product name appears as branding text.

### Out-of-Scope

- Renaming repository slug, package/module names, import paths, or API compatibility terms that must remain technical identifiers.
- Changing runtime code behavior or endpoint names.
- Rewriting legal ownership/contact terms unless explicitly requested later.

---

## Proposed Solution

### Overview

Perform a targeted documentation sweep across root markdown docs and `docs/` localized markdown files, replacing only branding usages of "Kiro Gateway" with "TrollLLM" while preserving technical identifiers (e.g., repo URL `kiro-gateway`, module/package names). Remove the explicit attribution line from docs README content.

### User Flow

1. Maintainer reads root or localized docs.
2. Product name consistently appears as TrollLLM.
3. Docs no longer include the `@jwadow` attribution line.

---

## Requirements

### Functional Requirements

#### Branding Replacement

All in-scope markdown docs must use TrollLLM for product branding text.

**Scenarios:**

- **WHEN** a root/docs markdown file contains branding text "Kiro Gateway" **THEN** it is replaced with "TrollLLM".
- **WHEN** "Kiro Gateway" appears as a technical identifier (repo slug, URL, compatibility label) **THEN** it is preserved.

#### Attribution Removal

The docs attribution line referencing `@jwadow` must be removed from docs README content.

**Scenarios:**

- **WHEN** the docs README contains the attribution line **THEN** that line is deleted.
- **WHEN** other references to `@jwadow` exist in legal/administrative docs **THEN** they are unchanged unless explicitly included in-scope.

### Non-Functional Requirements

- **Performance:** N/A (documentation-only change).
- **Security:** No credential or secret exposure in docs edits.
- **Accessibility:** Markdown readability and heading structure remain valid.
- **Compatibility:** Keep technical identifiers unchanged to avoid broken links/commands.

---

## Success Criteria

- [ ] All in-scope root/docs markdown branding mentions are updated to TrollLLM.
  - Verify: `rg -n "Kiro Gateway" README.md CONTRIBUTING.md docs AGENTS.md`
- [ ] Attribution line to `@jwadow` is removed from docs README content.
  - Verify: `rg -n "Made with|@Jwadow|@jwadow" README.md docs`
- [ ] Only documentation files are modified.
  - Verify: `git diff --name-only`

---

## Technical Context

### Existing Patterns

- `README.md:3` uses product branding in title format.
- `docs/*/README.md:3` localizations mirror branding in the same heading structure.
- `docs/en/ARCHITECTURE.md:1` and `docs/ru/ARCHITECTURE.md:1` include architecture titles with product name.

### Key Files

- `README.md` - Root primary documentation, includes branding and attribution.
- `docs/en/README.md` - English docs landing page pattern used by localized versions.
- `docs/ja/README.md` - Example localized README with branding line.
- `docs/en/ARCHITECTURE.md` - Technical docs title includes branding.

### Affected Files

Files this bead is expected to modify:

```yaml
files:
  - README.md
  - CONTRIBUTING.md
  - docs/en/README.md
  - docs/es/README.md
  - docs/id/README.md
  - docs/ja/README.md
  - docs/ko/README.md
  - docs/pt/README.md
  - docs/ru/README.md
  - docs/zh/README.md
  - docs/en/ARCHITECTURE.md
  - docs/ru/ARCHITECTURE.md
```

---

## Risks & Mitigations

| Risk                                            | Likelihood | Impact | Mitigation                                                                          |
| ----------------------------------------------- | ---------- | ------ | ----------------------------------------------------------------------------------- |
| Replacing technical identifiers unintentionally | Medium     | High   | Limit replacements to branding contexts and review diffs line-by-line.              |
| Missing localized occurrences                   | Medium     | Medium | Use repository-wide grep across `docs/` and root markdown files before/after edits. |
| Over-editing legal references                   | Low        | Medium | Keep `CLA.md` and legal sections out of scope unless explicitly requested.          |

---

## Open Questions

| Question                                                                                           | Owner      | Due Date       | Status |
| -------------------------------------------------------------------------------------------------- | ---------- | -------------- | ------ |
| Should `AGENTS.md` branding text be renamed in this bead or tracked separately due process impact? | Maintainer | During `/ship` | Open   |

---

## Tasks

### Identify in-scope branding occurrences [analysis]

An explicit file-and-line inventory exists for branding text and attribution targets in root/docs before any edits begin.

**Metadata:**

```yaml
depends_on: []
parallel: true
conflicts_with: []
files:
  - README.md
  - CONTRIBUTING.md
  - docs/en/README.md
  - docs/es/README.md
  - docs/id/README.md
  - docs/ja/README.md
  - docs/ko/README.md
  - docs/pt/README.md
  - docs/ru/README.md
  - docs/zh/README.md
  - docs/en/ARCHITECTURE.md
  - docs/ru/ARCHITECTURE.md
```

**Verification:**

- `rg -n "Kiro Gateway|@Jwadow|@jwadow|Made with" README.md CONTRIBUTING.md docs`

### Apply branding and attribution documentation edits [docs]

All in-scope markdown files show TrollLLM branding and the docs attribution line is removed without altering technical identifiers.

**Metadata:**

```yaml
depends_on: ["Identify in-scope branding occurrences"]
parallel: false
conflicts_with: []
files:
  - README.md
  - CONTRIBUTING.md
  - docs/en/README.md
  - docs/es/README.md
  - docs/id/README.md
  - docs/ja/README.md
  - docs/ko/README.md
  - docs/pt/README.md
  - docs/ru/README.md
  - docs/zh/README.md
  - docs/en/ARCHITECTURE.md
  - docs/ru/ARCHITECTURE.md
```

**Verification:**

- `git diff -- README.md CONTRIBUTING.md docs`
- `rg -n "Kiro Gateway" README.md CONTRIBUTING.md docs`

### Run final docs consistency checks [verification]

Validation evidence confirms no unintended files changed and no targeted branding/attribution residue remains in the intended scope.

**Metadata:**

```yaml
depends_on: ["Apply branding and attribution documentation edits"]
parallel: false
conflicts_with: []
files:
  - README.md
  - CONTRIBUTING.md
  - docs/en/README.md
  - docs/es/README.md
  - docs/id/README.md
  - docs/ja/README.md
  - docs/ko/README.md
  - docs/pt/README.md
  - docs/ru/README.md
  - docs/zh/README.md
  - docs/en/ARCHITECTURE.md
  - docs/ru/ARCHITECTURE.md
```

**Verification:**

- `git diff --name-only`
- `rg -n "Made with|@Jwadow|@jwadow" README.md docs`

---

## Notes

- This PRD defines specification only for `/create`; implementation begins later with `/start bd-2gw` then `/ship bd-2gw`.
- Current bead state indicates `bd-2gw` already exists in open status and is the correct target for this spec.

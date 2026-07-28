# ProjectHub V2 — Implementation Plan

**Status:** Complete (all milestones delivered)  
**Source of truth:** `docs/v2/PRD.md`, `DATA_MODEL.md`, `UX.md`, `API_CONTRACT.md`  
**Rule:** Do not invent features. Do not preserve V1 behaviour where it conflicts with V2. Stop after each milestone for review.

---

## Locked decisions

| Decision | Choice |
|----------|--------|
| Data strategy | **Greenfield** — no V1 content backfill, no synthetic Version 1, no Progress→Release Notes mapping |
| Schema approach | **Additive then cleanup** — V1 tables kept through M5; dropped in M6 |
| Gate | Stop after each milestone; do not continue without explicit approval |

---

## Reuse inventory

| Keep / reuse | Adapted | Removed (M6) |
|--------------|---------|--------------|
| Auth, workspace bootstrap, JWT deps | `projects` (+ `latest_version_number`; overview → draft) | Live `files` / `resources` tables |
| Ownership helper, error envelope | Share public resolve (≥1 version) | `progress_entries` + Progress UI |
| Signed-URL storage client | Storage copy-on-publish; draft vs version keys | V1 live file/resource/progress routes |
| Harbor UI, app shell, session client | Owner FE tabs; portal payload | `projects.overview` column |

---

## Milestone spine

```
M1 Schema models → M2 Draft APIs → M3 Publish/Versions → M4 Share/Portal API → M5 Owner FE → M6 Portal FE + cleanup
```

| Milestone | Scope | Status |
|-----------|--------|--------|
| **M1** | This plan + Alembic additive schema + SQLAlchemy V2 models + `latest_version_number` + limits scaffolding | **Complete (approved)** |
| **M2** | Draft APIs (overview/files/resources); project create seeds `project_drafts`; stop writing delivery overview to `projects.overview` | **Complete (approved)** |
| **M3** | Publish + Versions APIs; storage copy-on-publish; dirty / `has_unpublished_changes` | **Complete (approved)** |
| **M4** | Share gate (≥1 version); public portal versioned payloads + download auth | **Complete (approved)** |
| **M5** | Owner FE: drop Progress tab; Draft tabs; Publish; History; badges; delete UX | **Complete (approved)** |
| **M6** | Portal FE rewrite; remove V1 live file/resource/progress routes; drop unused tables | **Complete — awaiting review** |

---

## M1 — Schema foundation

**Status:** Complete (approved)

---

## M2 — Draft APIs

**Status:** Complete (approved)

---

## M3 — Publish & Versions

**Status:** Complete (approved)

---

## M4 — Share & Public Portal

**Status:** Complete (approved)

---

## M5 — Owner Frontend

**Status:** Complete (approved)

---

## M6 — Client Portal Migration & V1 Cleanup (current stop)

**In scope**
- Client Portal FE on V2 public APIs (latest + version switcher + versioned download)
- Portal hierarchy: Release notes → Overview → Resources → Files; hide empty sections
- Unmount V1 live `/files`, `/resources`, `/progress` routes and delete related services/repos/schemas
- Drop ORM models for V1 `File` / `Resource` / `ProgressEntry` and `projects.overview`
- Alembic `0003_v1_cleanup`: drop `files`, `resources`, `progress_entries`, `projects.overview`
- Remove dead Progress owner route directory; V2-aligned empty dashboard copy

**Out of scope**
- New product features beyond V2 docs
- V1 content backfill

**Acceptance**
1. Portal loads from published versions only; version switcher works when multiple versions exist.
2. V1 live content routes/tables/columns are gone.
3. Backend imports / app boot and frontend `tsc --noEmit` pass.
4. Stop for final review.

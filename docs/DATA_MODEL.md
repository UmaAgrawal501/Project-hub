# ProjectHub — Data Model (Version 1)

**Status:** Draft for review (Engineering Design)  
**Audience:** Backend architecture, engineering  
**Scope:** Conceptual data model only — no SQL, no ORM, no application code  
**Sources of truth (frozen):** `docs/PRD.md`, `docs/UX.md`, `docs/DESIGN_SYSTEM.md`

**Goals:** Simplest production-ready schema. Normalized. No premature optimization. Nothing outside the PRD.

**Auth note:** Identity is owned by **Supabase Auth**. The `users` entity below is the application profile keyed to the Auth user id — not a parallel password store.

---

## Design Principles

1. **Hierarchy:** User → Workspace → Project → (Files | Resources | Progress | Share).  
2. **UUIDs** for all primary keys.  
3. **Timestamps** on every persisted entity (`created_at`; `updated_at` where mutable).  
4. **Soft delete projects only** (`deleted_at`). Child rows remain until project is hard-purged (out of V1 UI) or cascade-cleaned by a later job.  
5. **One share row per project** (enable / disable / regenerate by updating that row).  
6. **Blobs stay in Supabase Storage**; the database stores metadata and storage paths only.  
7. **Enums as closed sets** matching product language.

---

# Entities

## 1. `users` (Application Profile)

**Purpose:** Owner identity for the product UI (name, email mirror) linked 1:1 with Supabase Auth.

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK; **equals** Supabase `auth.users.id` |
| `email` | String | Required | Unique; synced from Auth on create/update |
| `display_name` | String | Required | Settings / UI |
| `created_at` | DateTime (UTC) | Required | Set on insert |
| `updated_at` | DateTime (UTC) | Required | Bump on profile change |

**Relationships**
- `users` 1 — 1..n `workspaces` (V1 product rule: **exactly one** workspace per user at runtime; enforced in app + unique DB constraint on owner).

**Soft delete:** None in V1. Account deletion (if ever) is a hard purge path defined later — not a V1 feature.

**Indexes**
- Unique: `email`  
- PK: `id`

---

## 2. `workspaces`

**Purpose:** Tenancy boundary. All projects belong to a workspace. Keeps future multi-member workspaces possible without rewriting ownership.

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK |
| `owner_user_id` | UUID | Required | FK → `users.id`; **Unique** in V1 (one workspace per owner) |
| `name` | String | Required | Default e.g. `"Personal"` on signup |
| `created_at` | DateTime (UTC) | Required | |
| `updated_at` | DateTime (UTC) | Required | |

**Relationships**
- N:1 `users` via `owner_user_id`  
- 1:N `projects`

**Soft delete:** None. Deleting a user/workspace is out of V1 scope.

**Indexes**
- Unique: `owner_user_id`  
- PK: `id`

---

## 3. `projects`

**Purpose:** Atomic product unit — the Client Project Workspace.

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK |
| `workspace_id` | UUID | Required | FK → `workspaces.id` |
| `name` | String | Required | Non-empty; max length product-defined (e.g. 120) |
| `overview` | Text / String | Optional | Client-facing description |
| `status` | Enum | Required | `active` \| `completed` \| `archived`; default `active` |
| `created_at` | DateTime (UTC) | Required | |
| `updated_at` | DateTime (UTC) | Required | Bump on any project field change |
| `deleted_at` | DateTime (UTC) | Optional | Soft delete; null = live |

**Status definitions (product)**
- `active` — in progress; shown on main dashboard default  
- `completed` — delivered; still accessible on dashboard  
- `archived` — hidden from main dashboard; owner can still open  

**Relationships**
- N:1 `workspaces`  
- 1:N `files`, `resources`, `progress_entries`  
- 1:0..1 `project_shares` (at most one share record)

**Soft delete strategy**
- Set `deleted_at` when owner deletes a project (if V1 exposes delete) **or** treat archive as non-delete; PRD emphasizes Archive for hide.  
- **Recommendation for V1:**  
  - **Archive** = status change only (`archived`).  
  - **Soft delete** (`deleted_at`) = reserved for true removal from owner UI (optional V1); default lists filter `deleted_at IS NULL`.  
- Soft-deleted projects: share must be treated as inactive (application rule: do not resolve public page).  
- Child rows are **not** soft-deleted individually when the project is soft-deleted.

**Indexes**
- `(workspace_id, deleted_at)` — list projects for owner  
- `(workspace_id, status)` — dashboard filters (partial on `deleted_at IS NULL` if supported)  
- PK: `id`

---

## 4. `files`

**Purpose:** Metadata for curated delivery documents stored in object storage.

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK |
| `project_id` | UUID | Required | FK → `projects.id` |
| `name` | String | Required | Display / original filename |
| `storage_path` | String | Required | Path/key inside Supabase Storage bucket; unique globally recommended |
| `mime_type` | String | Required | e.g. `application/pdf` |
| `size_bytes` | Integer | Required | ≥ 1; enforce product max in app |
| `created_at` | DateTime (UTC) | Required | Upload time |
| `uploaded_by_user_id` | UUID | Required | FK → `users.id` (owner; future-proof) |

**Relationships**
- N:1 `projects`  
- N:1 `users` (uploader)

**Soft delete strategy**
- **Hard delete** on remove: delete DB row **and** storage object.  
- No `deleted_at` on files in V1 (keeps “curated delivery” simple).

**Indexes**
- `(project_id, created_at DESC)` — list files  
- Unique: `storage_path`  
- PK: `id`

---

## 5. `resources`

**Purpose:** Permanent typed reference links for the project.

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK |
| `project_id` | UUID | Required | FK → `projects.id` |
| `title` | String | Required | Non-empty |
| `url` | String | Required | Valid URL (app-validated) |
| `type` | Enum | Required | See enum below |
| `description` | String | Optional | Short note |
| `position` | Integer | Required | Sort order; default 0; unique per project optional |
| `created_at` | DateTime (UTC) | Required | |
| `updated_at` | DateTime (UTC) | Required | |

**`type` enum (closed set for V1)**  
`github` | `figma` | `production` | `staging` | `api_docs` | `postman` | `database_diagram` | `drive` | `other`

**Relationships**
- N:1 `projects`

**Soft delete strategy**
- **Hard delete** on remove.

**Indexes**
- `(project_id, position)` — ordered list  
- PK: `id`

---

## 6. `progress_entries`

**Purpose:** Client-facing progress timeline (“what’s the latest?”). Named to match product language **Progress** (not “updates”).

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK |
| `project_id` | UUID | Required | FK → `projects.id` |
| `title` | String | Required | Non-empty |
| `description` | Text / String | Required | Body; allow empty string only if product insists — **recommend Required non-empty** for quality |
| `created_at` | DateTime (UTC) | Required | Timeline sort key (newest first) |
| `updated_at` | DateTime (UTC) | Required | Edit timestamp |
| `created_by_user_id` | UUID | Required | FK → `users.id` |

**Relationships**
- N:1 `projects`  
- N:1 `users`

**Soft delete strategy**
- **Hard delete** on remove.

**Indexes**
- `(project_id, created_at DESC)` — timeline  
- PK: `id`

**Note on description:** PRD lists Title, Description, Created Date. Edits bump `updated_at` but public timeline still sorts by `created_at` unless product later chooses otherwise — **V1 sorts by `created_at` DESC**.

---

## 7. `project_shares`

**Purpose:** Single public access grant for a project (one link lifecycle).

| Field | Type | Req | Constraints / Notes |
|-------|------|-----|---------------------|
| `id` | UUID | Required | PK |
| `project_id` | UUID | Required | FK → `projects.id`; **Unique** (one row per project) |
| `token` | String | Required | Unique; high-entropy URL-safe secret (e.g. 32+ bytes encoded) |
| `is_enabled` | Boolean | Required | Default `false` until owner enables sharing |
| `created_at` | DateTime (UTC) | Required | First share record creation |
| `updated_at` | DateTime (UTC) | Required | Bump on enable/disable/regenerate |

**Relationships**
- 1:1 `projects`

**Soft delete strategy**
- Row is kept. Disable = `is_enabled = false`. Soft-deleted or missing project → public resolver fails.  
- No token history table in V1; regenerate **overwrites** `token`.

**Indexes**
- Unique: `project_id`  
- Unique: `token` (public lookup)  
- PK: `id`

---

# Enumerations Summary

| Enum | Values |
|------|--------|
| `project_status` | `active`, `completed`, `archived` |
| `resource_type` | `github`, `figma`, `production`, `staging`, `api_docs`, `postman`, `database_diagram`, `drive`, `other` |

---

# 1. Entity Relationship Diagram (ERD)

```
┌──────────────────┐
│      users       │
│ (profile = auth) │
└────────┬─────────┘
         │ 1
         │
         │ owns
         │
         │ N (V1: N=1)
┌────────▼─────────┐
│    workspaces    │
└────────┬─────────┘
         │ 1
         │
         │ contains
         │
         │ N
┌────────▼─────────┐         ┌──────────────────┐
│     projects     │1──────0..1│  project_shares  │
│  (soft delete)   │         │  (token gate)    │
└────────┬─────────┘         └──────────────────┘
         │
         │ 1
         │
    ┌────┴─────┬──────────────┐
    │          │              │
    │ N        │ N            │ N
┌───▼───┐ ┌────▼─────┐ ┌──────▼──────────┐
│ files │ │ resources│ │ progress_entries│
│(meta) │ │  (links) │ │   (timeline)    │
└───┬───┘ └──────────┘ └──────┬──────────┘
    │                         │
    │ storage_path            │
    ▼                         │
┌────────────────┐            │
│ Supabase       │            │
│ Storage bucket │            │
│ (objects)      │            │
└────────────────┘            │
                              │
         users also referenced as uploaded_by / created_by
```

---

# 2. Table Definitions (Logical)

Logical tables (names as above):

| Table | Primary key | Notable uniques | Delete behavior |
|-------|-------------|-----------------|-----------------|
| `users` | `id` | `email` | None (V1) |
| `workspaces` | `id` | `owner_user_id` | None (V1) |
| `projects` | `id` | — | Soft (`deleted_at`) |
| `files` | `id` | `storage_path` | Hard + storage object |
| `resources` | `id` | — | Hard |
| `progress_entries` | `id` | — | Hard |
| `project_shares` | `id` | `project_id`, `token` | Row retained; disable/regenerate |

**Referential actions (logical)**
- Delete workspace → restrict in V1 (should not happen).  
- Hard delete project (admin/purge) → cascade delete children + share + storage objects.  
- Soft delete project → **no** cascade; children orphaned from UI only.

---

# 3. Relationship Explanation

| From | To | Cardinality | Meaning |
|------|----|-------------|---------|
| User | Workspace | 1:1 (V1) | Tenancy root created at signup |
| Workspace | Project | 1:N | All owner projects |
| Project | File | 1:N | Delivery documents |
| Project | Resource | 1:N | Permanent links |
| Project | Progress entry | 1:N | Client timeline |
| Project | Share | 1:0..1 | Optional until first enable; then 1:1 row |
| User | File | 1:N | Uploader audit |
| User | Progress | 1:N | Author audit |

**Public access path (no user session):**  
`token` → `project_shares` (enabled) → `projects` (not soft-deleted) → child collections read-only.

**Private access path:**  
Auth user → `users.id` → `workspaces.owner_user_id` → `projects.workspace_id` → children.  
Every private query must be scoped by workspace ownership.

---

# 4. Data Lifecycle

### Owner signup
1. Supabase Auth creates auth user.  
2. App creates `users` profile (`id` = auth id).  
3. App creates `workspaces` row (`owner_user_id` unique).

### Project create
1. Insert `projects` (`status = active`, `deleted_at = null`).  
2. No share row yet **or** insert `project_shares` with `is_enabled = false` and a pre-generated token (either is fine; **recommend create share row lazily on first Enable**).

### Workspace population
- Files: upload to Storage → insert `files` metadata.  
- Resources: insert/update/delete rows.  
- Progress: insert/update/delete rows; list by `created_at DESC`.

### Status changes
- Active ↔ Completed ↔ Archived via `projects.status` only.  
- Archived projects remain readable by owner; excluded from default dashboard filter.

### Project soft delete (if exposed)
1. Set `projects.deleted_at = now()`.  
2. Force-disable share (`is_enabled = false`) in the same operation.  
3. Children retained; public token stops resolving.

### File remove
1. Delete Storage object at `storage_path`.  
2. Hard delete `files` row.  
3. If storage delete fails, do not leave orphan metadata without a retry/compensation path (application concern).

### Account / workspace teardown
- Out of V1 scope. Document later: cascade purge Storage prefixes + all tables.

---

# 5. File Storage Strategy

| Concern | Decision |
|---------|----------|
| Provider | Supabase Storage |
| Bucket | Private bucket e.g. `project-files` |
| Object key | `{workspace_id}/{project_id}/{file_id}/{safe_filename}` |
| DB stores | `storage_path`, `name`, `mime_type`, `size_bytes` |
| Access (owner) | Authenticated backend issues short-lived signed URL after ownership check |
| Access (client) | Backend validates share token + `is_enabled` + project not deleted → signed URL |
| Public bucket | **No** — never world-readable objects |
| Size / type limits | Enforced in application (PRD/UX curated delivery); not DB triggers |
| Thumbnails / virus scan | Out of V1 |

**Invariant:** Database is source of truth for *whether* a file exists in product; Storage holds bytes. Orphan detection can be a later ops task — not V1 scope.

---

# 6. Share Token Lifecycle

```
[No row] 
    │ Enable sharing (first time)
    ▼
[Row exists, is_enabled=true, token=T1]
    │ Copy link → /p/{T1}  (path shape is UX/routing; token is the secret)
    │
    ├─ Disable ──────────► is_enabled=false  (T1 useless until re-enable)
    │                         │
    │                      Enable again ──► is_enabled=true (same T1 unless regenerated)
    │
    └─ Regenerate ───────► token=T2, is_enabled=true, updated_at=now
                              T1 invalid immediately (no history table)
```

**Rules**
1. At most **one** `project_shares` row per project.  
2. Public resolver requires: token match AND `is_enabled = true` AND project `deleted_at IS NULL`.  
3. Soft-deleted or archived projects: product may still allow share if enabled — **recommend:** Archived may remain shareable; **soft-deleted must not**. Status `archived` alone does not disable share.  
4. Token: cryptographically random, URL-safe, unguessable; never sequential ids.  
5. Regenerating updates `token` in place; old URLs 404 / “link no longer active”.  
6. No client accounts; no per-client ACL rows.

---

# What We Explicitly Do Not Model (V1)

- Teams, roles, permissions tables  
- Comments, notifications, activity audit log  
- File version history  
- Folders / tags / full-text search indexes  
- Billing / subscriptions  
- Share token history / password-protected shares  
- Multiple workspaces per user  
- Client user records  

---

# Consistency Rules (Application-Level)

These are data rules enforced by services, not extra tables:

1. Private mutations only if `workspace.owner_user_id == auth user`.  
2. Enabling share on a soft-deleted project is rejected.  
3. Quotas (files per project, max size) enforced before insert/upload.  
4. Resource `url` must be `http`/`https`.  
5. Dashboard default query: `deleted_at IS NULL AND status IN (active, completed)` with filter UI for archived.

---

# Handoff

This document is the **data model source of truth** once approved.

**Next engineering design steps (when you approve):** API contract design → backend module design → then implementation milestones — still no code until a milestone is approved.

Do not invent extra entities during implementation without an explicit product/engineering change request.

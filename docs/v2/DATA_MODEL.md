# ProjectHub V2 — Data Model

**Status:** Approved conceptual model (aligned with V2 PRD)  
**Depends on:** `docs/v2/PRD.md`  
**Scope:** Conceptual data model only — no SQL, no ORM, no application code  
**Hard rule:** Client Portal and all public reads use **immutable Version snapshots only**. Draft tables/rows are never public.

**Auth note:** Identity is owned by Supabase Auth. `users` is the application profile keyed to Auth user id.

---

## Design principles

1. **Hierarchy:** User → Workspace → Project → (Draft content | Versions | Share).  
2. **UUIDs** for primary keys.  
3. **Timestamps** on persisted entities.  
4. **Soft delete projects only** (`deleted_at`). Versions and draft rows are not soft-deleted independently.  
5. **One share row per published Version** (version-locked delivery link).  

6. **Blobs in object storage**; DB stores metadata and storage keys.  
7. **Versions are append-only.** No updates to version snapshot rows after insert.  
8. **Draft ≠ Version.** Separate storage of mutable vs immutable content.  
9. **Project `name` is snapshotted into each Version at publish.** Portal delivery name always reads the Version.  
10. **Project `status` is live only.** Not stored on Versions. Portal status always reads the Project.  
11. **Draft modelling is Option A only** (tables below). No alternate draft shapes.

---

## Enumerations

| Enum | Values |
|------|--------|
| `project_status` | `active`, `completed`, `archived` |
| `resource_type` | `github`, `figma`, `production`, `staging`, `api_docs`, `postman`, `database_diagram`, `drive`, `other` |

---

## Validation limits (normative)

| Field | Limit |
|-------|-------|
| `projects.name` | 1–120 characters after trim |
| `project_drafts.overview` / `project_versions.overview` | null, or 0–10_000 characters after trim; empty after trim → null |
| `project_versions.name` | 1–120 characters (copied from project at publish) |
| `project_versions.release_notes` | 1–10_000 characters after trim |
| `users.display_name` | 1–80 characters after trim |
| Draft file `size_bytes` | ≤ 25 MiB (26_214_400 bytes) |
| Draft files per project | ≤ 50 |
| `draft_resources.title` / version resource title | 1–120 |
| Resource `url` | http or https; ≤ 2048 |
| Resource `description` | optional; ≤ 2000 |
| Resource `position` | integer ≥ 0 |

MIME allowlist for draft uploads: `application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `application/zip`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/plain`.

---

## 1. `users`

| Field | Notes |
|-------|--------|
| `id` | PK; equals Auth user id |
| `email` | Required |
| `display_name` | 1–80 |
| `created_at` / `updated_at` | |

**Relationships:** 1:1 workspace (one workspace per owner).

---

## 2. `workspaces`

| Field | Notes |
|-------|--------|
| `id` | PK |
| `owner_user_id` | Unique FK → users |
| `name` | |
| `created_at` / `updated_at` | |

**Relationships:** 1:N `projects`.

---

## 3. `projects`

Atomic engagement container. Live owner fields only for name and status.

| Field | Notes |
|-------|--------|
| `id` | PK |
| `workspace_id` | FK |
| `name` | Required; 1–120; owner-facing live name; **copied into Version at publish** |
| `status` | `project_status`; **live only; not versioned** |
| `created_at` / `updated_at` | |
| `deleted_at` | Soft delete; null = active row |
| `latest_version_number` | Nullable int; null = never published; denormalized for dashboard |

**Relationships:** 1:1 `project_drafts`; 1:N `draft_files`; 1:N `draft_resources`; 1:N `project_versions`; 1:N `project_shares` (one per published version).

**Portal rules:**
- Portal **name** does **not** come from this row at read time — it comes from `project_versions.name` for the selected version.  
- Portal **status** comes from this row (when project is not soft-deleted).  
- Soft-deleted projects (`deleted_at` set) are excluded from owner lists and fail all public resolve checks.  
- `completed` and `archived` do **not** block share or portal access.

---

## 4. Draft content (Option A — normative)

Draft is modeled **only** as the following project-scoped tables.

### 4a. `project_drafts` (1:1 project)

| Field | Notes |
|-------|--------|
| `project_id` | PK/FK → projects |
| `overview` | Nullable text; ≤ 10_000 after trim; empty → null |
| `updated_at` | Bumped on overview change and may be bumped when draft files/resources change |

Created empty when the project is created.

### 4b. `draft_files`

| Field | Notes |
|-------|--------|
| `id` | PK |
| `project_id` | FK |
| `name` | Display filename |
| `storage_path` | Private draft object key |
| `mime_type` | Allowlisted |
| `size_bytes` | ≤ 25 MiB |
| `created_at` | |
| `uploaded_by_user_id` | FK users |

Hard delete on remove. Storage object removed with the row (draft only). Max 50 rows per project.

### 4c. `draft_resources`

| Field | Notes |
|-------|--------|
| `id` | PK |
| `project_id` | FK |
| `title` | 1–120 |
| `url` | http(s) ≤ 2048 |
| `type` | `resource_type` |
| `description` | Optional ≤ 2000 |
| `position` | ≥ 0 |
| `created_at` / `updated_at` | |

Hard delete on remove.

**Indexes:** `(project_id, …)` as needed for list order (e.g. resources by `position`, files by `created_at`).

---

## 5. `project_versions` (immutable headers)

| Field | Notes |
|-------|--------|
| `id` | PK |
| `project_id` | FK |
| `version_number` | Int ≥ 1; unique per project |
| `name` | **Snapshot of `projects.name` at publish**; 1–120; immutable |
| `release_notes` | Required; 1–10_000 after trim |
| `overview` | Snapshot of draft overview at publish (nullable) |
| `published_at` | UTC |
| `published_by_user_id` | FK users |

**Constraints:** Unique `(project_id, version_number)`.  
**Soft delete:** None — versions persist while the project row exists (including soft-deleted projects).  
**Updates:** Forbidden after insert (append-only).

---

## 6. Version snapshots (immutable children)

### 6a. `version_files`

| Field | Notes |
|-------|--------|
| `id` | PK; globally unique UUID |
| `version_id` | FK → `project_versions` |
| `name`, `mime_type`, `size_bytes` | Copied from draft file metadata |
| `storage_path` | Path to **immutable** object in the version key namespace |
| `created_at` | Set at publish |

**Public download authorization** keys off `version_files.id` belonging to a Version of the project resolved by the share token (see API Contract).

### 6b. `version_resources`

| Field | Notes |
|-------|--------|
| `id` | PK |
| `version_id` | FK |
| `title`, `url`, `type`, `description`, `position` | Copied from draft |

**Immutability:** Rows never updated. On publish, each draft file object is **copied** into a distinct version storage key (copy-on-publish). Draft uploads must never overwrite version keys.

---

## 7. `project_shares`

| Field | Notes |
|-------|--------|
| `id` | PK |
| `project_id` | FK → projects (not unique — many shares per project) |
| `version_number` | Int ≥ 1; unique with `project_id` — locks this token to that Version |
| `token` | Unique URL-safe secret |
| `is_enabled` | Bool |
| `created_at` / `updated_at` | |

**Created on Publish:** each successful publish inserts an enabled share for the new `version_number`.

**Public resolve requires all of:**
1. Share row exists for token  
2. `is_enabled = true`  
3. Project `deleted_at` is null  
4. The share’s `version_number` exists as a published Version for the project  

The portal for a token serves **only** that frozen Version (no jump to latest, no switcher to other versions).

`status` being `completed` or `archived` does **not** fail resolve.

Owner **disable** sets `is_enabled = false` on **all** shares for the project. **Regenerate** overwrites `token` on the share for `latest_version_number` only (older version links untouched). Soft-delete sets `is_enabled = false` on all shares for the project.

---

## 8. ERD (conceptual)

```
users 1──1 workspaces 1──N projects
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        project_drafts  draft_files  draft_resources
              │
              │ publish (copies name + overview + files + resources)
              ▼
        project_versions 1──N version_files
              │            1──N version_resources
              │
        project_shares (0..N; one per version)
```

---

## 9. Publish invariant

On successful publish of project P:

1. Reject if project is soft-deleted.  
2. Validate Draft is publishable: at least one of: overview with length > 0 after trim; ≥1 `draft_files`; ≥1 `draft_resources`.  
3. Validate `release_notes` non-empty after trim (1–10_000).  
4. Insert `project_versions` with `version_number = coalesce(max(version_number), 0) + 1`, `name = projects.name` (current), `overview` = draft overview snapshot, `release_notes`, `published_at`, `published_by_user_id`.  
5. Copy each draft resource into `version_resources`.  
6. For each draft file: copy storage object into immutable version keyspace; insert `version_files`.  
7. Set `projects.latest_version_number` to the new number.  
8. Insert an enabled `project_shares` row for that `version_number` (new unique token).  
9. Commit atomically at the DB layer; do not commit a Version that points at missing version file bytes.

Draft rows remain; owner continues editing. Concurrent publish races that would duplicate `version_number` must fail with conflict (unique constraint).

---

## 10. Dirty / unpublished changes (normative)

| Condition | `has_unpublished_changes` | Dashboard badge |
|-----------|---------------------------|-----------------|
| `latest_version_number` is null | **false** | **Not published** |
| `latest_version_number` is N and Draft content equals Version N (overview, files set, resources set) | **false** | **vN** |
| `latest_version_number` is N and Draft content differs from Version N | **true** | **vN** + **Unpublished changes** |

**Never published is not dirty.**

Dirty comparison covers Draft overview, draft file set (identity/content as engineering implements via hash or structural compare), and draft resource set — not project `status`. Live `name` changes **do** count as dirty relative to the snapshotted Version `name` (because the next publish will snapshot a different name).

Computation method (content hash, structural compare, etc.) is an implementation detail; the boolean semantics above are product-normative.

---

## 11. What V2 removes vs V1 model

| V1 | V2 |
|----|----|
| Live `files` / `resources` / `progress_entries` as public source | Draft tables + version snapshots |
| `progress_entries` | **Removed** — replaced by `release_notes` on versions |
| Public reads live project content fields | Public reads versions only (name from version; status from live project) |

---

## 12. Approval checkpoint

This Data Model is aligned with the V2 PRD. No migrations or application code until engineering kickoff is approved.

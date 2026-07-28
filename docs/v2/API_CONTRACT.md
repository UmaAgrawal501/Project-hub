# ProjectHub V2 — API Contract

**Status:** Approved API specification (aligned with V2 PRD / Data Model / UX)  
**Depends on:** `docs/v2/PRD.md`, `docs/v2/DATA_MODEL.md`  
**Scope:** HTTP API shapes only — no implementation  
**Hard rule:** Every **public** response is built from **immutable published versions** (except live `status`). Public handlers must not read draft tables.

Base path: `/api/v1` (URI prefix may remain; product is V2).  
Format: JSON. Auth: Bearer access token unless marked Public.  
Timestamps: ISO-8601 UTC strings.

---

## 1. Conventions

### Success envelope

```json
{ "data": {} }
```

Collections: `data` is an array. List endpoints that support pagination include:

```json
{
  "data": [],
  "meta": { "limit": 20, "offset": 0, "total": 0 }
}
```

### Error envelope

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": [{ "field": "string", "message": "string", "code": "string" }]
  }
}
```

`details` is present for `validation_error`; may be omitted otherwise.

### Common codes

| HTTP | code |
|------|------|
| 400 | `validation_error` |
| 401 | `unauthorized`, `invalid_credentials` |
| 404 | `not_found`, `share_unavailable`, `share_not_initialized` |
| 409 | `conflict`, `project_deleted`, `nothing_to_publish`, `file_limit_reached` |
| 413 | `file_too_large` |
| 415 | `unsupported_media_type` |
| 500 | `internal_error` |

### Security

- Workspace ownership on all private project routes.  
- Soft-deleted projects: treat as `not_found` for owner reads/lists; use `409 project_deleted` when an action explicitly cannot proceed because the project is deleted (e.g. publish, share enable).  
- **Never** return `storage_path`, bucket names, or service keys.  
- **Never** include draft fields on public payloads.  
- Public error message for portal failures: do not leak why the link is unavailable.

### Dirty flag semantics (all private responses that expose it)

| Condition | `has_unpublished_changes` |
|-----------|---------------------------|
| `latest_version_number` is null | `false` |
| `latest_version_number` is N and Draft equals Version N (including snapshotted name vs live name) | `false` |
| `latest_version_number` is N and Draft differs from Version N | `true` |

Never published is never dirty.

---

## 2. Validation limits (normative)

| Field | Rules |
|-------|-------|
| Project `name` | Required on create; 1–120 after trim |
| Draft / version `overview` | null or string; max 10_000 after trim; empty after trim → null |
| `release_notes` | Required on publish; 1–10_000 after trim |
| User `display_name` | 1–80 after trim |
| Draft file size | ≤ 26_214_400 bytes (25 MiB) |
| Draft files per project | ≤ 50 |
| Resource `title` | 1–120 |
| Resource `url` | must be `http` or `https`; ≤ 2048 |
| Resource `description` | optional; ≤ 2000; empty → null |
| Resource `position` | integer ≥ 0 |
| New password | ≥ 8 characters |

**MIME allowlist (draft upload):**  
`application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `application/zip`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/plain`.

---

## 3. Response schemas (normative)

All private/public payloads use these shapes. Fields marked optional may be null or omitted only where stated.

### 3.1 User

| Field | Type |
|-------|------|
| `id` | uuid string |
| `email` | string |
| `display_name` | string |
| `created_at` | datetime |
| `updated_at` | datetime |

### 3.2 Workspace

| Field | Type |
|-------|------|
| `id` | uuid string |
| `name` | string |
| `created_at` | datetime |
| `updated_at` | datetime |

### 3.3 ShareSummary

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid string | |
| `project_id` | uuid string | |
| `version_number` | integer | Locked Version this token serves |
| `token` | string | |
| `is_enabled` | boolean | |
| `public_path` | string | `/p/{token}` |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 3.4 ProjectSummary

Used by `GET /projects`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid string | |
| `workspace_id` | uuid string | |
| `name` | string | Live name |
| `status` | `active` \| `completed` \| `archived` | Live |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `latest_version_number` | integer \| null | null = never published |
| `has_unpublished_changes` | boolean | See dirty semantics |

### 3.5 DraftSummary

Embedded on project detail — not full file/resource lists.

| Field | Type | Notes |
|-------|------|-------|
| `overview` | string \| null | |
| `updated_at` | datetime | |
| `has_unpublished_changes` | boolean | Same semantics as project |
| `file_count` | integer | ≥ 0 |
| `resource_count` | integer | ≥ 0 |

### 3.6 ProjectDetail

Used by `GET /projects/{project_id}` and returned (as `ProjectDetail`) from create when useful; create may return the same shape.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid string | |
| `workspace_id` | uuid string | |
| `name` | string | Live |
| `status` | `active` \| `completed` \| `archived` | Live |
| `created_at` | datetime | |
| `updated_at` | datetime | |
| `latest_version_number` | integer \| null | |
| `has_unpublished_changes` | boolean | |
| `draft` | DraftSummary | Always present for non-deleted projects |
| `share` | ShareSummary \| null | Share for `latest_version_number`, or null if never published |

`Project` as used in create success is **identical to `ProjectDetail`**.

### 3.7 Draft

Used by get/patch draft.

| Field | Type |
|-------|------|
| `overview` | string \| null |
| `updated_at` | datetime |
| `has_unpublished_changes` | boolean |

### 3.8 DraftFile

| Field | Type |
|-------|------|
| `id` | uuid string |
| `project_id` | uuid string |
| `name` | string |
| `mime_type` | string |
| `size_bytes` | integer |
| `created_at` | datetime |

### 3.9 DraftResource

| Field | Type |
|-------|------|
| `id` | uuid string |
| `project_id` | uuid string |
| `title` | string |
| `url` | string |
| `type` | resource_type enum |
| `description` | string \| null |
| `position` | integer |
| `created_at` | datetime |
| `updated_at` | datetime |

### 3.10 VersionSummary

Used by owner `GET .../versions`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid string | |
| `project_id` | uuid string | |
| `version_number` | integer | ≥ 1 |
| `name` | string | Snapshotted project name |
| `release_notes` | string | Full text |
| `overview` | string \| null | Full text on list (clients may truncate in UI) |
| `published_at` | datetime | |

Order: `version_number` **descending**.

### 3.11 Version

Full version header (owner get + publish response).

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid string | |
| `project_id` | uuid string | |
| `version_number` | integer | |
| `name` | string | Snapshotted at publish |
| `release_notes` | string | |
| `overview` | string \| null | |
| `published_at` | datetime | |
| `published_by_user_id` | uuid string | Owner context only; omit on public |

### 3.12 VersionFile

| Field | Type |
|-------|------|
| `id` | uuid string |
| `name` | string |
| `mime_type` | string |
| `size_bytes` | integer |
| `created_at` | datetime |

No `storage_path`. No `project_id` required on wire.

### 3.13 VersionResource

| Field | Type |
|-------|------|
| `id` | uuid string |
| `title` | string |
| `url` | string |
| `type` | resource_type enum |
| `description` | string \| null |
| `position` | integer |

### 3.14 PublicVersionRef

| Field | Type |
|-------|------|
| `version_number` | integer |
| `published_at` | datetime |

### 3.15 PublicPortalProject

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | From **selected Version snapshot** |
| `status` | `active` \| `completed` \| `archived` | From **live project** |

### 3.16 PublicPortalVersion

| Field | Type |
|-------|------|
| `version_number` | integer |
| `name` | string |
| `release_notes` | string |
| `overview` | string \| null |
| `published_at` | datetime |

### 3.17 PublicFile / PublicResource

Same fields as `VersionFile` / `VersionResource`.

### 3.18 DownloadUrl

| Field | Type |
|-------|------|
| `download_url` | string |
| `expires_at` | datetime |
| `name` | string |

---

## 4. Auth APIs

| Method | Route | Auth | Notes |
|--------|-------|------|-------|
| POST | `/auth/sign-up` | No | Creates profile + workspace |
| POST | `/auth/sign-in` | No | |
| POST | `/auth/sign-out` | Yes | |
| POST | `/auth/forgot-password` | No | |
| POST | `/auth/reset-password` | No | |
| GET | `/auth/me` | Yes | `{ user, workspace }` |
| PATCH | `/auth/me` | Yes | `display_name` only |
| POST | `/auth/change-password` | Yes | current + new password |

### Bodies

**POST `/auth/sign-up`**  
`{ "email": string, "password": string, "display_name": string }`  
**201:**

```json
{
  "data": {
    "user": { "...User..." },
    "workspace": { "...Workspace..." },
    "session": {
      "access_token": "string",
      "refresh_token": "string",
      "expires_in": 3600,
      "token_type": "bearer"
    }
  }
}
```

(Session wrapper matches the auth stack response. Both `access_token` and `refresh_token` are required for session continuity.)

**POST `/auth/sign-in`**  
`{ "email": string, "password": string }`  
**200:** same session shape as sign-up.

**POST `/auth/sign-out`** → `{ "data": { "ok": true } }`

**POST `/auth/forgot-password`**  
`{ "email": string }` → `{ "data": { "ok": true } }` (always ok; no email enumeration)

**POST `/auth/reset-password`**  
`{ "token": string, "password": string }` → `{ "data": { "ok": true } }`

**GET `/auth/me`** → `{ "data": { "user": User, "workspace": Workspace } }`

**PATCH `/auth/me`**  
`{ "display_name": string }` → `{ "data": { "user": User } }`

**POST `/auth/change-password`**  
`{ "current_password": string, "new_password": string }` → `{ "data": { "ok": true } }`

---

## 5. Projects (container)

### 5.1 List projects

`GET /projects?status=active|completed|archived&limit&offset`

**Auth:** Yes  

**Success 200:** `{ "data": [ ProjectSummary ], "meta": { "limit", "offset", "total" } }`  

Only rows with `deleted_at IS NULL`. Default `status=active` if omitted. Default `limit=20`, max `100`.

### 5.2 Create project

`POST /projects`  

Body:

| Field | Required | Rules |
|-------|----------|-------|
| `name` | Yes | 1–120 after trim |
| `overview` | No | Seeds Draft overview; null/empty → null |

**Success 201:** `{ "data": ProjectDetail }`  
Creates Draft. Does **not** create a Version. `latest_version_number` is null; `has_unpublished_changes` is false; `share` is null.

### 5.3 Get project

`GET /projects/{project_id}`  

**Success 200:** `{ "data": ProjectDetail }`  
**404** `not_found` if missing, not owned, or soft-deleted.

### 5.4 Patch project

`PATCH /projects/{project_id}`  

Body: any of:

| Field | Rules |
|-------|-------|
| `name` | 1–120 after trim |
| `status` | `active` \| `completed` \| `archived` |

Overview edits use Draft APIs only.

**Success 200:** `{ "data": ProjectDetail }`  
Changing `name` when a Version exists may set `has_unpublished_changes` to true.

### 5.5 Soft delete

`DELETE /projects/{project_id}`  

Sets `deleted_at`; sets `is_enabled=false` on all share rows for the project.  

**Success 200:** `{ "data": { "ok": true } }`  
**404** if already deleted / not found.

---

## 6. Draft APIs (private)

All require auth + ownership. Soft-deleted → `404 not_found` (or `409 project_deleted` where stated). Mutate/read **draft only**.

### 6.1 Get draft

`GET /projects/{project_id}/draft`  

**Success 200:** `{ "data": Draft }`

### 6.2 Update draft overview

`PATCH /projects/{project_id}/draft`  

Body: `{ "overview": string | null }`  

**Success 200:** `{ "data": Draft }`

### 6.3 Draft files

| Method | Route | Notes |
|--------|-------|-------|
| GET | `/projects/{project_id}/draft/files` | `{ "data": [ DraftFile ] }` |
| POST | `/projects/{project_id}/draft/files/upload-url` | Signed upload intent |
| POST | `/projects/{project_id}/draft/files/confirm` | Persist draft file metadata |
| POST | `/projects/{project_id}/draft/files/{file_id}/download-url` | Owner download |
| DELETE | `/projects/{project_id}/draft/files/{file_id}` | Delete draft file + draft storage object |

**POST upload-url** body:

| Field | Required | Rules |
|-------|----------|-------|
| `name` | Yes | filename string |
| `mime_type` | Yes | allowlist |
| `size_bytes` | Yes | 1..25 MiB |

**Success 200:**

```json
{
  "data": {
    "upload_url": "string",
    "token": "string",
    "expires_at": "datetime"
  }
}
```

(`token` is the opaque confirm handle; never a storage path.)

**Errors:** `415 unsupported_media_type`, `413 file_too_large`, `409 file_limit_reached`.

**POST confirm** body:

| Field | Required |
|-------|----------|
| `token` | Yes |
| `name` | Yes |
| `mime_type` | Yes |
| `size_bytes` | Yes |

**Success 201:** `{ "data": DraftFile }`

**POST download-url** → `{ "data": DownloadUrl }`  
**DELETE** → `{ "data": { "ok": true } }`

### 6.4 Draft resources

| Method | Route | Success |
|--------|-------|---------|
| GET | `/projects/{project_id}/draft/resources` | `{ "data": [ DraftResource ] }` ordered by `position` ascending |
| POST | `/projects/{project_id}/draft/resources` | **201** `{ "data": DraftResource }` |
| PATCH | `/projects/{project_id}/draft/resources/{resource_id}` | **200** `{ "data": DraftResource }` |
| DELETE | `/projects/{project_id}/draft/resources/{resource_id}` | `{ "data": { "ok": true } }` |

**POST/PATCH body fields:** `title`, `url`, `type`, `description?`, `position?` with validation limits in §2.

---

## 7. Publish & Versions (private)

### 7.1 Publish

`POST /projects/{project_id}/publish`  

Body:

| Field | Required | Rules |
|-------|----------|-------|
| `release_notes` | Yes | 1–10_000 after trim |

**Behavior:** Create next immutable Version from current Draft + current live `projects.name`. Copy-on-publish for files. Update `latest_version_number`. Mint a new enabled share token locked to that `version_number`.

**Success 201:**

```json
{
  "data": {
    "version": { "...Version..." },
    "files": [ { "...VersionFile..." } ],
    "resources": [ { "...VersionResource..." } ],
    "share": { "...ShareSummary..." }
  }
}
```

**Errors:**
- `400` `validation_error` — empty/invalid release notes  
- `409` `nothing_to_publish` — no trimmed overview, no draft files, no draft resources  
- `409` `project_deleted`  
- `409` `conflict` — concurrent publish / unique version_number race  
- `404` / `401` / `500`

Republish with identical Draft content and new release notes is allowed. Each publish returns a **new** `share` (prior version links remain valid and stay locked to their versions).

### 7.2 List versions

`GET /projects/{project_id}/versions`  

**Success 200:** `{ "data": [ VersionSummary ] }`  
Order: `version_number` descending (highest first).

### 7.3 Get version

`GET /projects/{project_id}/versions/{version_number}`  

**Success 200:**

```json
{
  "data": {
    "version": { "...Version..." },
    "files": [ { "...VersionFile..." } ],
    "resources": [ { "...VersionResource..." } ]
  }
}
```

**404** if version_number not found for project.

### 7.4 Owner download from version

`POST /projects/{project_id}/versions/{version_number}/files/{file_id}/download-url`  

`file_id` must be a `version_files.id` belonging to that project version.  

**Success 200:** `{ "data": DownloadUrl }`  
**404** `not_found` otherwise.

---

## 8. Share (private)

| Method | Route | Behavior |
|--------|-------|----------|
| GET | `/projects/{project_id}/shares` | `{ "data": [ ShareSummary ] }` — all delivery links, `version_number` descending |
| GET | `/projects/{project_id}/share` | `{ "data": { "enabled": boolean, "share": ShareSummary \| null } }` — share for `latest_version_number` (or null) |
| POST | `/projects/{project_id}/share/enable` | Enable share for `latest_version_number` (create if missing after publish); `409` if never published or soft-deleted |
| POST | `/projects/{project_id}/share/disable` | Set `is_enabled=false` on **all** shares; `404 share_not_initialized` if no rows |
| POST | `/projects/{project_id}/share/regenerate` | New token on **latest** Version’s share only; older links untouched; `404 share_not_initialized` if no latest share |

**Success shapes:** enable / regenerate / disable return `{ "data": { "enabled": boolean, "share": ShareSummary } }` (`share` = latest Version’s row after the mutation).

Shares are minted on **Publish**. Enable does **not** publish.  
`completed` and `archived` projects may use share endpoints.

---

## 9. Public Client Portal APIs

**Auth:** None.

### Public availability (all public routes)

Return `404` `share_unavailable` when any of:
- Unknown / regenerated token  
- That share disabled  
- Project soft-deleted  
- Locked `version_number` missing for the project  

Do **not** fail solely because `status` is `completed` or `archived`.

Client-facing message: link no longer active (no internal reason).

### 9.1 Get portal (locked version)

`GET /public/{token}`  

Resolves the Version equal to the share row’s `version_number` (not project latest).

**Success 200:**

```json
{
  "data": {
    "project": {
      "name": "string",
      "status": "active|completed|archived"
    },
    "version": {
      "version_number": 1,
      "name": "string",
      "release_notes": "string",
      "overview": "string|null",
      "published_at": "datetime"
    },
    "resources": [ { "...PublicResource..." } ],
    "files": [ { "...PublicFile..." } ],
    "versions_available": [ { "version_number": 1, "published_at": "datetime" } ]
  }
}
```

**Field sources (normative):**
- `project.name` = **locked Version** `name` (same as `version.name`)  
- `project.status` = **live** `projects.status`  
- `version.*`, `resources`, `files` = that Version’s immutable snapshot  
- `versions_available` = **only** the locked Version (`PublicVersionRef`); clients cannot switch to other versions via this token  

### 9.2 Get portal specific version

`GET /public/{token}/versions/{version_number}`  

Same payload as 9.1 **only if** `version_number` equals the share’s locked version.  
`404 share_unavailable` if token invalid under §9 rules **or** `version_number` ≠ share.version_number.

### 9.3 Public file download

`POST /public/{token}/files/{file_id}/download-url`  

Body:

| Field | Required | Rules |
|-------|----------|-------|
| `version_number` | No | If provided, must equal the share’s locked version; if omitted, use the locked version |

**Authorization algorithm (normative):**

1. Resolve share by token; apply public availability checks (§9).  
2. Let `V` = Version for the share’s `version_number`. If body `version_number` is provided and differs → `404 share_unavailable`. If Version does not exist → `404 share_unavailable`.  
3. Load `version_files` row where `id = file_id` **and** `version_id = V.id`.  
4. If no row → `404 share_unavailable` (do not leak whether the file exists on another version).  
5. Issue short-lived signed download URL for that row’s immutable storage object.

`file_id` is always a **version file id**, never a draft file id. Draft file ids must never authorize public downloads.

**Success 200:** `{ "data": DownloadUrl }`  
**Errors:** `404 share_unavailable` only for auth/resolve failures on this route (including missing file on the locked version).

---

## 10. Endpoint inventory (V2)

**Auth:** sign-up, sign-in, sign-out, forgot-password, reset-password, me (GET/PATCH), change-password  

**Projects:** list, create, get, patch, delete  

**Draft:** get/patch draft; draft files (list, upload-url, confirm, download-url, delete); draft resources (CRUD)  

**Versions:** publish, list, get, version file download-url  

**Share:** list, get, enable, disable, regenerate  

**Public:** get locked version, get version (same lock only), file download-url  

**Health:** `GET /health` allowed  

**Out of contract:** Progress CRUD; live project files/resources as public source; version mutation/delete; draft exposure on public routes.

---

## 11. Approval checkpoint

This contract is aligned with the V2 PRD, UX, and Data Model. **No implementation until engineering kickoff is approved.**

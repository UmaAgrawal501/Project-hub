# ProjectHub — API Contract (Version 1)

**Status:** Draft for review  
**Audience:** Frontend and backend engineering  
**Role:** Single source of truth for the HTTP API between client and server  
**Scope:** Contract only — no application code, SQL, ORM, or vendor SDK usage  

**Frozen inputs (do not contradict):**

- `docs/PRD.md`
- `docs/UX.md`
- `docs/DESIGN_SYSTEM.md`
- `docs/DATA_MODEL.md`

**Base URL:** `/api/v1`  
**Protocols:** HTTPS only in production  
**Format:** JSON (`Content-Type: application/json`) unless noted for upload binary transfer to object storage

---

# 1. API Design Principles

## Style

- RESTful resource-oriented routes
- JSON request and response bodies
- UUID string identifiers for all entity ids
- All timestamps are ISO-8601 UTC with `Z` suffix (example: `2026-07-28T07:30:00Z`)
- snake_case for JSON fields
- Plural collection nouns (`/projects`, `/files`)
- No RPC-style verbs in paths except where product actions are not CRUD (`/share/enable`, password flows)

## Consistent success envelope

Every successful response uses:

```json
{
  "data": {}
}
```

- Single resource: `data` is an object
- Collections: `data` is an array
- Optional pagination meta (when used):

```json
{
  "data": [],
  "meta": {
    "limit": 50,
    "offset": 0,
    "total": 12
  }
}
```

No success message string required when `data` is sufficient.

## Consistent error envelope

Every error response uses:

```json
{
  "error": {
    "code": "string_error_code",
    "message": "Human-readable summary",
    "details": []
  }
}
```

`details` is an array of field errors when applicable:

```json
{
  "field": "name",
  "message": "Name is required",
  "code": "required"
}
```

`details` may be an empty array.

## HTTP status codes

| Status | Meaning |
|--------|---------|
| `200` | OK — read or update success |
| `201` | Created |
| `204` | No Content — successful delete with empty body (allowed alternative: `200` + `{ "data": { "ok": true } }`; **V1 standard: `200` + `{ "data": { "ok": true } }` for JSON clients) |
| `400` | Validation / bad request |
| `401` | Unauthenticated |
| `403` | Authenticated but not allowed |
| `404` | Resource not found (or not visible) |
| `409` | Conflict (duplicate email, state conflict) |
| `413` | Payload too large (file) |
| `415` | Unsupported media type (file) |
| `429` | Rate limited |
| `500` | Internal error (no internal details exposed) |

## Authentication strategy

- Owner identity is provided by **Supabase Auth** (see Data Model).
- Private endpoints require header:

  `Authorization: Bearer {access_token}`

- The API validates the access token, resolves the application `users` profile and the owner’s single `workspaces` row.
- Auth endpoints in this contract are part of the **backend API surface** so the frontend has one contract. The backend is responsible for integrating with the identity provider; clients do not need a second API style for V1.

## Authorization rules

| Actor | Access |
|-------|--------|
| Owner (valid Bearer token) | Full CRUD within **own workspace** only |
| Client (no account) | Read-only via **share token** on public routes only |
| Anyone else | Denied |

Rules:

1. Workspace isolation: every private project/file/resource/progress/share mutation must verify `project.workspace_id` belongs to the token user’s workspace.
2. Soft-deleted projects (`deleted_at` set) are invisible on private list/get except where explicitly documented; public routes never resolve them.
3. Share public routes require `project_shares.is_enabled = true` and a matching token.
4. Clients never receive owner-only fields beyond the public models defined below.
5. Storage paths are **never** returned in any response.

---

# 2. Authentication APIs

## 2.1 Sign Up

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/auth/sign-up` |
| **Description** | Create owner account, profile, and personal workspace |
| **Auth required** | No |

**Request body**

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `display_name` | string | Yes | 1–80 chars |
| `email` | string | Yes | Valid email |
| `password` | string | Yes | Min length per security policy (min 8) |

**Success `201`**

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

**Errors**

| Status | Code | When |
|--------|------|------|
| `400` | `validation_error` | Invalid fields |
| `409` | `email_taken` | Email already registered |
| `429` | `rate_limited` | Too many attempts |
| `500` | `internal_error` | Unexpected failure |

---

## 2.2 Sign In

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/auth/sign-in` |
| **Description** | Authenticate owner and return session |
| **Auth required** | No |

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `email` | string | Yes |
| `password` | string | Yes |

**Success `200`**

Same shape as Sign Up (`user`, `workspace`, `session`).

**Errors**

| Status | Code | When |
|--------|------|------|
| `400` | `validation_error` | Missing fields |
| `401` | `invalid_credentials` | Email/password incorrect (generic message) |
| `429` | `rate_limited` | Too many attempts |
| `500` | `internal_error` | Unexpected failure |

---

## 2.3 Sign Out

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/auth/sign-out` |
| **Description** | Invalidate current session / refresh credential as applicable |
| **Auth required** | Yes |

**Request body:** empty object `{}` or none.

**Success `200`**

```json
{
  "data": { "ok": true }
}
```

**Errors:** `401` `unauthorized`; `500` `internal_error`

---

## 2.4 Forgot Password

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/auth/forgot-password` |
| **Description** | Request password reset email |
| **Auth required** | No |

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `email` | string | Yes |

**Success `200`**

```json
{
  "data": {
    "ok": true,
    "message": "If an account exists for this email, a reset link has been sent."
  }
}
```

Always returns the same success shape whether or not the email exists (anti-enumeration).

**Errors:** `400` `validation_error`; `429` `rate_limited`; `500` `internal_error`

---

## 2.5 Reset Password

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/auth/reset-password` |
| **Description** | Set a new password using the reset token from email |
| **Auth required** | No (token in body) |

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `token` | string | Yes |
| `password` | string | Yes |

**Success `200`**

```json
{
  "data": { "ok": true }
}
```

**Errors:** `400` `validation_error`; `400` `invalid_or_expired_token`; `429` `rate_limited`; `500` `internal_error`

---

## 2.6 Get Current User

| | |
|---|---|
| **Method** | `GET` |
| **Route** | `/api/v1/auth/me` |
| **Description** | Return authenticated user and workspace |
| **Auth required** | Yes |

**Success `200`**

```json
{
  "data": {
    "user": { "...User..." },
    "workspace": { "...Workspace..." }
  }
}
```

**Errors:** `401` `unauthorized`; `500` `internal_error`

---

## 2.7 Update Current User (Settings)

| | |
|---|---|
| **Method** | `PATCH` |
| **Route** | `/api/v1/auth/me` |
| **Description** | Update display name (Settings) |
| **Auth required** | Yes |

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `display_name` | string | Yes |

**Success `200`:** `{ "data": { "user": { "...User..." } } }`

**Errors:** `400` `validation_error`; `401` `unauthorized`; `500` `internal_error`

---

## 2.8 Change Password (Settings)

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/auth/change-password` |
| **Description** | Change password while authenticated |
| **Auth required** | Yes |

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `current_password` | string | Yes |
| `new_password` | string | Yes |

**Success `200`:** `{ "data": { "ok": true } }`

**Errors:** `400` `validation_error`; `401` `unauthorized` / `invalid_credentials`; `500` `internal_error`

---

# 3. Project APIs

All project routes: **Auth required: Yes**, private, workspace-scoped.  
Soft-deleted projects are excluded from list/get unless noted.  
`DELETE` performs soft delete (`deleted_at`) and disables sharing.

Status transitions (Complete / Archive / Restore) use `PATCH` with `status`. There are no separate `/archive` routes.

| Semantic (UX) | API |
|---------------|-----|
| Complete | `PATCH` `{ "status": "completed" }` |
| Archive | `PATCH` `{ "status": "archived" }` |
| Restore to Active | `PATCH` `{ "status": "active" }` |
| Mark Active (from Completed) | `PATCH` `{ "status": "active" }` |

---

## 3.1 List Projects

| | |
|---|---|
| **Method** | `GET` |
| **Route** | `/api/v1/projects` |
| **Description** | List owner projects for dashboard filters |
| **Auth required** | Yes |

**Query**

| Param | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `status` | string | No | `active` | One of: active, completed, archived |
| `limit` | int | No | `50` | Max `100` |
| `offset` | int | No | `0` | |

Only projects with `deleted_at = null`.

**Success `200`**

```json
{
  "data": [ { "...ProjectSummary..." } ],
  "meta": { "limit": 50, "offset": 0, "total": 3 }
}
```

Default sort: `updated_at` descending.

**Errors:** `400` `validation_error`; `401` `unauthorized`; `500` `internal_error`

---

## 3.2 Create Project

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/projects` |
| **Description** | Create project (`status=active`) |
| **Auth required** | Yes |

**Request body**

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | 1–120 chars |
| `overview` | string | No | Max 10_000 chars |

**Success `201`**

```json
{
  "data": { "...Project..." }
}
```

Share row is **not** required at create (lazy on first enable).

**Errors:** `400` `validation_error`; `401` `unauthorized`; `500` `internal_error`

---

## 3.3 Get Project

| | |
|---|---|
| **Method** | `GET` |
| **Route** | `/api/v1/projects/{project_id}` |
| **Description** | Get project detail for workspace shell / Overview |
| **Auth required** | Yes |

**Success `200`:** `{ "data": { "...Project..." } }`  
May include nested `share` summary when a share row exists (see `Share` model); if none, `share: null`.

**Errors:** `401`; `403` (other workspace); `404` (missing or soft-deleted); `500`

---

## 3.4 Update Project (Overview / Status)

| | |
|---|---|
| **Method** | `PATCH` |
| **Route** | `/api/v1/projects/{project_id}` |
| **Description** | Update name, overview, and/or status |
| **Auth required** | Yes |

**Request body** (at least one field)

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | No | 1–120 chars |
| `overview` | string or null | No | Max 10_000; `null` clears |
| `status` | string | No | `active` or `completed` or `archived` |

**Success `200`:** `{ "data": { "...Project..." } }`

**Errors:** `400`; `401`; `403`; `404`; `500`

---

## 3.5 Delete Project (Soft Delete)

| | |
|---|---|
| **Method** | `DELETE` |
| **Route** | `/api/v1/projects/{project_id}` |
| **Description** | Soft-delete project; force-disable share |
| **Auth required** | Yes |

**Success `200`:** `{ "data": { "ok": true } }`

**Side effects (contractual):** set `deleted_at`; if share exists, set `is_enabled=false`.

**Errors:** `401`; `403`; `404`; `500`

---

# 4. File APIs

Private, auth required, project ownership required.  
Upload uses a **signed upload URL** flow so browsers put bytes directly to object storage. The API never returns `storage_path`.

## 4.1 V1 platform limits

| Limit | Value |
|-------|-------|
| Max file size | 25 MiB |
| Max files per project | 50 |
| Allowed MIME types | See list below |

**Allowed MIME types**

- `application/pdf`
- `image/png`
- `image/jpeg`
- `image/webp`
- `image/gif`
- `application/zip`
- `application/msword`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- `application/vnd.ms-excel`
- `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `text/plain`

Reject with `413` / `415` / `400` as appropriate before or at confirm time.

---

## 4.2 List Files

| | |
|---|---|
| **Method** | `GET` |
| **Route** | `/api/v1/projects/{project_id}/files` |
| **Auth required** | Yes |

**Success `200`:** `{ "data": [ { "...File..." } ] }`  
Sort: `created_at` descending.

**Errors:** `401`; `403`; `404` (project); `500`

---

## 4.3 Create Upload Intent (Signed Upload URL)

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/projects/{project_id}/files/upload-url` |
| **Description** | Validate limits and return a short-lived signed upload URL |
| **Auth required** | Yes |

**Request body**

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | Yes | Original filename, 1–255 chars |
| `mime_type` | string | Yes | Must be allowed |
| `size_bytes` | integer | Yes | 1..25 MiB |

**Success `200`**

```json
{
  "data": {
    "upload_url": "https://signed-upload-url",
    "upload_token": "opaque_string_for_confirm",
    "expires_at": "2026-07-28T07:35:00Z",
    "required_headers": {
      "Content-Type": "application/pdf"
    }
  }
}
```

Notes:

- `upload_token` is an opaque server-issued value bound to project + declared metadata (not a storage path).
- Client uploads binary to `upload_url` using the method required by storage (typically `PUT`).
- This response must not include bucket keys or storage paths.

**Errors**

| Status | Code | When |
|--------|------|------|
| `400` | `validation_error` | Bad metadata |
| `403` / `404` | | Project access |
| `409` | `file_limit_reached` | Already 50 files |
| `413` | `file_too_large` | Size over limit |
| `415` | `unsupported_media_type` | MIME not allowed |
| `500` | `internal_error` | |

---

## 4.4 Confirm Upload

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/projects/{project_id}/files/confirm` |
| **Description** | After successful storage upload, persist file metadata |
| **Auth required** | Yes |

**Request body**

| Field | Type | Required |
|-------|------|----------|
| `upload_token` | string | Yes |
| `name` | string | Yes |
| `mime_type` | string | Yes |
| `size_bytes` | integer | Yes |

Server verifies object exists, size/MIME match intent, enforces limits, creates `files` row.

**Success `201`:** `{ "data": { "...File..." } }`

**Errors:** `400` `validation_error` / `upload_not_found` / `upload_mismatch`; `409` `file_limit_reached`; `401`; `403`; `404`; `500`

---

## 4.5 Get Download URL (Owner)

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/projects/{project_id}/files/{file_id}/download-url` |
| **Description** | Issue short-lived signed download URL for owner |
| **Auth required** | Yes |

**Request body:** none / `{}`

**Success `200`**

```json
{
  "data": {
    "download_url": "https://signed-download-url",
    "expires_at": "2026-07-28T07:35:00Z",
    "name": "Proposal.pdf"
  }
}
```

**Errors:** `401`; `403`; `404`; `500`

---

## 4.6 Delete File

| | |
|---|---|
| **Method** | `DELETE` |
| **Route** | `/api/v1/projects/{project_id}/files/{file_id}` |
| **Description** | Hard-delete metadata and storage object |
| **Auth required** | Yes |

**Success `200`:** `{ "data": { "ok": true } }`

**Errors:** `401`; `403`; `404`; `500`

---

## 4.7 Signed URL flow (summary)

1. `POST .../files/upload-url` → client receives `upload_url` + `upload_token`  
2. Client uploads bytes to `upload_url`  
3. `POST .../files/confirm` → `File` resource  
4. Download anytime via `POST .../download-url` (owner) or public download endpoint (client)

---

# 5. Resource APIs

Auth required. Ownership required.

**Validation**

| Field | Rules |
|-------|-------|
| `title` | Required, 1–120 chars |
| `url` | Required, `http` or `https` URL, max 2048 chars |
| `type` | Required enum: `github`, `figma`, `production`, `staging`, `api_docs`, `postman`, `database_diagram`, `drive`, `other` |
| `description` | Optional, max 2000 chars |
| `position` | Integer ≥ 0; used for ordering |

**Ordering:** List ascending by `position`, then `created_at` ascending as tiebreaker.

---

## 5.1 List Resources

`GET /api/v1/projects/{project_id}/resources` → `200` `{ "data": [ Resource ] }`

---

## 5.2 Create Resource

`POST /api/v1/projects/{project_id}/resources`

**Body:** `title`, `url`, `type`, `description?`  
If `position` omitted, append to end (max existing position + 1).

**Success `201`:** `{ "data": { Resource } }`

---

## 5.3 Update Resource

`PATCH /api/v1/projects/{project_id}/resources/{resource_id}`

**Body:** any of `title`, `url`, `type`, `description`, `position`

**Success `200`:** `{ "data": { Resource } }`

---

## 5.4 Delete Resource

`DELETE /api/v1/projects/{project_id}/resources/{resource_id}`  
**Success `200`:** `{ "data": { "ok": true } }`  
Hard delete.

---

## 5.5 Reorder Resources (optional convenience)

`PUT /api/v1/projects/{project_id}/resources/order`

**Body:**

```json
{
  "resource_ids": ["uuid", "uuid"]
}
```

Must include every resource id for the project exactly once. Assigns `position` by array index.

**Success `200`:** `{ "data": [ Resource ] }`

**Errors:** `400` if set mismatch.

> If V1 frontend only edits `position` via PATCH, this endpoint may be deferred; both are allowed by contract. Prefer implementing **PATCH position** minimum; add reorder endpoint if drag-and-drop ships.

---

# 6. Progress APIs

Auth required. Ownership required.

**Validation**

| Field | Rules |
|-------|-------|
| `title` | Required, 1–160 chars |
| `description` | Required, 1–10_000 chars |

**Ordering:** `created_at` descending (newest first). Edits do not change sort key.

---

## 6.1 List Progress

`GET /api/v1/projects/{project_id}/progress`  
**Success `200`:** `{ "data": [ ProgressEntry ] }`

---

## 6.2 Create Progress

`POST /api/v1/projects/{project_id}/progress`  
**Body:** `title`, `description`  
**Success `201`:** `{ "data": { ProgressEntry } }`

---

## 6.3 Update Progress

`PATCH /api/v1/projects/{project_id}/progress/{progress_id}`  
**Body:** `title?`, `description?` (at least one)  
**Success `200`:** `{ "data": { ProgressEntry } }`

---

## 6.4 Delete Progress

`DELETE /api/v1/projects/{project_id}/progress/{progress_id}`  
**Success `200`:** `{ "data": { "ok": true } }`  
Hard delete.

---

# 7. Share APIs

## Private share management (owner)

### 7.1 Get Share State

`GET /api/v1/projects/{project_id}/share`  
**Auth:** Yes  

**Success `200`**

- If no row yet: `{ "data": { "enabled": false, "share": null } }`
- If row exists: `{ "data": { "enabled": true|false, "share": { Share } } }`

---

### 7.2 Enable Sharing

`POST /api/v1/projects/{project_id}/share/enable`  
**Auth:** Yes  
**Body:** none / `{}`

**Behavior**

- If no row: create `project_shares` with new token, `is_enabled=true` (lazy create)
- If row exists: set `is_enabled=true` (token unchanged)
- Reject if project soft-deleted

**Success `200`:** `{ "data": { "share": { Share } } }`

**Errors:** `404`; `409` `project_deleted`; `401`; `403`; `500`

---

### 7.3 Disable Sharing

`POST /api/v1/projects/{project_id}/share/disable`  
**Auth:** Yes  

Sets `is_enabled=false`. Token retained until regenerate.

**Success `200`:** `{ "data": { "share": { Share } } }`  
**Errors:** `404` if no share row yet (`share_not_initialized`); `401`; `403`; `500`

---

### 7.4 Regenerate Token

`POST /api/v1/projects/{project_id}/share/regenerate`  
**Auth:** Yes  

Issues new token; previous token invalid immediately; sets `is_enabled=true`.

**Success `200`:** `{ "data": { "share": { Share } } }`  
**Errors:** `404` if never enabled (`share_not_initialized`); `401`; `403`; `500`

---

## Public share access (client, no auth)

Public path prefix: `/api/v1/public`

### 7.5 Get Public Project

| | |
|---|---|
| **Method** | `GET` |
| **Route** | `/api/v1/public/{token}` |
| **Description** | Full read-only workspace payload for Public Share Page |
| **Auth required** | No |

**Success `200`**

```json
{
  "data": {
    "project": { "...PublicProject..." },
    "resources": [ { "...PublicResource..." } ],
    "progress": [ { "...PublicProgressEntry..." } ],
    "files": [ { "...PublicFile..." } ]
  }
}
```

**Section order for clients (UX):** Overview (in `project`) → Progress → Resources → Files.  
API may return objects in any key order; frontend renders per UX.

**Errors**

| Status | Code | When |
|--------|------|------|
| `404` | `share_unavailable` | Unknown token, disabled, regenerated old token, or project soft-deleted |

Message should match UX: link no longer active — do not leak whether project exists.

---

### 7.6 Public File Download URL

| | |
|---|---|
| **Method** | `POST` |
| **Route** | `/api/v1/public/{token}/files/{file_id}/download-url` |
| **Auth required** | No |

**Success `200`:** same shape as owner download URL (`download_url`, `expires_at`, `name`)

**Errors:** `404` `share_unavailable` or file not in project; `500`

No list/upload/delete on public API beyond this contract.

---

# 8. Response Models

Fields marked optional may be `null`.

## User

| Field | Type |
|-------|------|
| `id` | uuid string |
| `email` | string |
| `display_name` | string |
| `created_at` | datetime |
| `updated_at` | datetime |

## Workspace

| Field | Type |
|-------|------|
| `id` | uuid string |
| `name` | string |
| `created_at` | datetime |
| `updated_at` | datetime |

## Project

| Field | Type |
|-------|------|
| `id` | uuid string |
| `workspace_id` | uuid string |
| `name` | string |
| `overview` | string or null |
| `status` | `active` or `completed` or `archived` |
| `created_at` | datetime |
| `updated_at` | datetime |
| `share` | Share or null (on get detail only; omit on list) |

## ProjectSummary

Same as Project **without** `share`. Used in list endpoints.

## File

| Field | Type |
|-------|------|
| `id` | uuid string |
| `project_id` | uuid string |
| `name` | string |
| `mime_type` | string |
| `size_bytes` | integer |
| `created_at` | datetime |

**Never include:** `storage_path`, bucket names, internal keys.

## Resource

| Field | Type |
|-------|------|
| `id` | uuid string |
| `project_id` | uuid string |
| `title` | string |
| `url` | string |
| `type` | resource type enum |
| `description` | string or null |
| `position` | integer |
| `created_at` | datetime |
| `updated_at` | datetime |

## ProgressEntry

| Field | Type |
|-------|------|
| `id` | uuid string |
| `project_id` | uuid string |
| `title` | string |
| `description` | string |
| `created_at` | datetime |
| `updated_at` | datetime |

## Share

| Field | Type |
|-------|------|
| `id` | uuid string |
| `project_id` | uuid string |
| `token` | string |
| `is_enabled` | boolean |
| `public_path` | string (relative route such as `/p/` + token) |
| `created_at` | datetime |
| `updated_at` | datetime |

Absolute public site origin is a frontend/env concern; API provides `token` + `public_path`.

## PublicProject

| Field | Type |
|-------|------|
| `name` | string |
| `overview` | string or null |
| `status` | `active` or `completed` or `archived` |
| `updated_at` | datetime |

No ids required for public project shell; optional `id` **omitted** in V1 public model to reduce leakage. Files/resources/progress still use ids for download/open actions.

## PublicFile

| Field | Type |
|-------|------|
| `id` | uuid string |
| `name` | string |
| `mime_type` | string |
| `size_bytes` | integer |
| `created_at` | datetime |

## PublicResource

| Field | Type |
|-------|------|
| `id` | uuid string |
| `title` | string |
| `url` | string |
| `type` | enum |
| `description` | string or null |
| `position` | integer |

## PublicProgressEntry

| Field | Type |
|-------|------|
| `id` | uuid string |
| `title` | string |
| `description` | string |
| `created_at` | datetime |

## Session

| Field | Type |
|-------|------|
| `access_token` | string |
| `refresh_token` | string |
| `expires_in` | integer (seconds) |
| `token_type` | `"bearer"` |

---

# 9. Error Models

## Standard error schema

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": [
      {
        "field": "string",
        "message": "string",
        "code": "string"
      }
    ]
  }
}
```

## Catalog

| HTTP | `error.code` | Meaning |
|------|--------------|---------|
| `400` | `validation_error` | Request failed validation |
| `400` | `invalid_or_expired_token` | Password reset token invalid |
| `400` | `upload_not_found` | Confirm called without valid upload |
| `400` | `upload_mismatch` | Confirm metadata does not match intent/object |
| `401` | `unauthorized` | Missing/invalid Bearer token |
| `401` | `invalid_credentials` | Sign-in / change-password failed |
| `403` | `forbidden` | Authenticated but not owner of resource |
| `404` | `not_found` | Private resource missing |
| `404` | `share_unavailable` | Public link dead/disabled/unknown |
| `404` | `share_not_initialized` | Disable/regenerate before enable |
| `409` | `email_taken` | Sign-up conflict |
| `409` | `file_limit_reached` | Max files per project |
| `409` | `project_deleted` | Illegal operation on soft-deleted project |
| `409` | `conflict` | Generic state conflict |
| `413` | `file_too_large` | Over size limit |
| `415` | `unsupported_media_type` | MIME not allowed |
| `429` | `rate_limited` | Too many requests |
| `500` | `internal_error` | Unexpected server failure |

**Rules**

- Never put stack traces, SQL, or storage paths in `message` or `details`
- Prefer stable `code` values for frontend branching
- Use generic credentials messages on auth failure

---

# 10. Security Rules

1. **Ownership validation:** Resolve user → workspace → project before any private mutation or read.  
2. **Workspace isolation:** Cross-workspace ids return `404` or `403` (V1 prefer `404` for project ids to avoid existence leaks across tenants).  
3. **Share token validation:** Constant-time compare where applicable; high-entropy tokens; public routes check `is_enabled` and project not soft-deleted.  
4. **Archived projects:** Remain owner-accessible and may remain publicly shareable if enabled (Data Model). Soft-deleted projects must not resolve publicly and cannot enable share.  
5. **Signed download URLs:** Short TTL (recommended 60–300 seconds); method/path constrained to one object.  
6. **Never expose storage paths,** bucket names, or internal upload keys in JSON.  
7. **Upload intent binding:** `upload_token` must be single-use or expire; confirm must verify object.  
8. **Rate limit** auth and public token endpoints.  
9. **CORS** only for known frontend origins.  
10. **No client write APIs** on public routes.

---

# 11. API Conventions

## Pagination

- Offset pagination: `limit`, `offset`, `meta.total`  
- Used on project list in V1  
- Nested project collections (files/resources/progress) return full arrays within V1 limits (max 50 files; resources/progress unbounded practically but expected small — optional future pagination not in V1)

## Sorting

| Collection | Default sort |
|------------|--------------|
| Projects | `updated_at DESC` |
| Files | `created_at DESC` |
| Resources | `position ASC`, `created_at ASC` |
| Progress | `created_at DESC` |

## Filtering

- Projects: `status` query param only in V1

## Date formats

- ISO-8601 UTC with `Z`

## Naming

- Routes: kebab-case for multi-word actions (`sign-up`, `download-url`)  
- JSON fields: snake_case  
- Enums: lowercase snake / lowercase words as defined  

## Idempotency

- `enable` when already enabled: success, same token  
- `disable` when already disabled: success  
- `DELETE` on already soft-deleted project: `404`

## Versioning

- Prefix `/api/v1`  
- Breaking changes require `/api/v2`

---

# 12. Endpoint Summary

| Method | Route | Purpose | Auth | Surface |
|--------|-------|---------|------|---------|
| `POST` | `/api/v1/auth/sign-up` | Register owner | No | Private API (public access) |
| `POST` | `/api/v1/auth/sign-in` | Login | No | Public access |
| `POST` | `/api/v1/auth/sign-out` | Logout | Yes | Private |
| `POST` | `/api/v1/auth/forgot-password` | Request reset email | No | Public access |
| `POST` | `/api/v1/auth/reset-password` | Reset password | No | Public access |
| `GET` | `/api/v1/auth/me` | Current user + workspace | Yes | Private |
| `PATCH` | `/api/v1/auth/me` | Update display name | Yes | Private |
| `POST` | `/api/v1/auth/change-password` | Change password | Yes | Private |
| `GET` | `/api/v1/projects` | List projects | Yes | Private |
| `POST` | `/api/v1/projects` | Create project | Yes | Private |
| `GET` | `/api/v1/projects/{project_id}` | Get project | Yes | Private |
| `PATCH` | `/api/v1/projects/{project_id}` | Update overview/status | Yes | Private |
| `DELETE` | `/api/v1/projects/{project_id}` | Soft-delete project | Yes | Private |
| `GET` | `/api/v1/projects/{project_id}/files` | List files | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/files/upload-url` | Signed upload intent | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/files/confirm` | Confirm upload | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/files/{file_id}/download-url` | Signed download | Yes | Private |
| `DELETE` | `/api/v1/projects/{project_id}/files/{file_id}` | Delete file | Yes | Private |
| `GET` | `/api/v1/projects/{project_id}/resources` | List resources | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/resources` | Create resource | Yes | Private |
| `PATCH` | `/api/v1/projects/{project_id}/resources/{resource_id}` | Update resource | Yes | Private |
| `DELETE` | `/api/v1/projects/{project_id}/resources/{resource_id}` | Delete resource | Yes | Private |
| `PUT` | `/api/v1/projects/{project_id}/resources/order` | Reorder resources | Yes | Private (optional) |
| `GET` | `/api/v1/projects/{project_id}/progress` | List progress | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/progress` | Create progress | Yes | Private |
| `PATCH` | `/api/v1/projects/{project_id}/progress/{progress_id}` | Edit progress | Yes | Private |
| `DELETE` | `/api/v1/projects/{project_id}/progress/{progress_id}` | Delete progress | Yes | Private |
| `GET` | `/api/v1/projects/{project_id}/share` | Get share state | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/share/enable` | Enable sharing | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/share/disable` | Disable sharing | Yes | Private |
| `POST` | `/api/v1/projects/{project_id}/share/regenerate` | Regenerate token | Yes | Private |
| `GET` | `/api/v1/public/{token}` | Public project payload | No | Public |
| `POST` | `/api/v1/public/{token}/files/{file_id}/download-url` | Public download URL | No | Public |

---

# Out of Scope for This API (V1)

Aligned with PRD / Data Model non-goals:

- Team/member endpoints  
- Comments, notifications, analytics  
- Billing  
- File versioning  
- Password-protected shares  
- Client accounts  
- Search endpoints  
- Admin/purge APIs  

---

# Handoff

Once approved, this document is the **API source of truth**.

Frontend and backend must implement against these routes, models, and error codes.

**Next engineering step (when approved):** Backend module/architecture design and/or frontend API client typing — still no implementation code until a milestone is explicitly approved.

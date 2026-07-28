# ProjectHub — Implementation Plan (Version 1)

**Status:** Awaiting approval — no code until approved  
**Inputs (frozen, do not modify):**  
`docs/PRD.md` · `docs/UX.md` · `docs/DESIGN_SYSTEM.md` · `docs/DATA_MODEL.md` · `docs/API_CONTRACT.md`

**Stack (locked):** Next.js + TypeScript + Tailwind + shadcn/ui · FastAPI + SQLAlchemy + Alembic · Supabase Postgres/Auth/Storage · Vercel + Render

---

## 0. Document consistency review

After reading all five documents end-to-end, the product is coherent. These items need **your decision** before or during early milestones (they are not new features — they resolve ambiguity):

| # | Topic | Observation | Proposed default if you approve the plan as-is |
|---|--------|-------------|----------------|
| A | Soft-delete project in UI | API + Data Model define `DELETE` soft-delete; UX/PRD emphasize **Archive**, wireframes show no Delete Project control | Ship API soft-delete; **do not expose Delete in UI in V1** — use Archive only. Soft-delete remains for later or admin. |
| B | Resource reorder endpoint | API marks `PUT .../resources/order` optional; UX has no drag-and-drop | **Defer** reorder endpoint; use create append + optional `PATCH position` only if needed |
| C | Email verification gate | UX mentions optional verify interstitial; API/PRD do not require it | **No verification gate** in V1; sign-up → dashboard |
| D | Reset password URL | API expects `token` in body; Supabase emails a link | Frontend `/reset-password?token=...` reads query and calls API |
| E | Fonts / icons deps | Harbor: Satoshi + IBM Plex Mono; icons Lucide-compatible; shadcn | Before Milestone 0 install: approve font strategy + shadcn/lucide (smallest footprint) |

No contradictions that block architecture. No invented endpoints or entities in this plan.

---

## 1. Project folder structure

Monorepo at repository root:

```
document_manager/
├── docs/                          # Frozen product/engineering docs (read-only)
├── frontend/                      # Next.js App Router (Vercel)
│   ├── app/
│   │   ├── (marketing)/           # Landing
│   │   ├── (auth)/                # Sign up, sign in, forgot, reset
│   │   ├── (app)/                 # Authenticated shell
│   │   │   ├── projects/          # Dashboard
│   │   │   ├── projects/[id]/    # Workspace + section routes
│   │   │   └── settings/
│   │   ├── p/[token]/            # Public share page
│   │   ├── layout.tsx
│   │   └── not-found.tsx
│   ├── components/
│   │   ├── ui/                    # shadcn primitives mapped to Harbor
│   │   ├── layout/                # AppTopBar, AccountMenu, WorkspaceHeader
│   │   ├── projects/
│   │   ├── files/
│   │   ├── resources/
│   │   ├── progress/
│   │   ├── share/
│   │   └── empty-states/
│   ├── features/                  # Optional feature modules (hooks + UI colocated)
│   ├── hooks/
│   ├── lib/
│   │   ├── api/                   # Typed API client (API_CONTRACT only)
│   │   ├── auth/                  # Token storage, session helpers
│   │   └── utils/
│   ├── styles/                    # Harbor tokens → CSS variables / Tailwind theme
│   └── package.json
├── backend/                       # FastAPI (Render)
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                   # Route handlers only (v1 routers)
│   │   │   └── v1/
│   │   ├── core/                  # Config, security, errors, deps
│   │   ├── database/              # Engine, session
│   │   ├── models/                # SQLAlchemy models (= DATA_MODEL)
│   │   ├── schemas/               # Pydantic req/res (= API_CONTRACT)
│   │   ├── repositories/
│   │   ├── services/              # Business logic
│   │   ├── storage/               # Supabase Storage signed URL helpers
│   │   └── utils/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt           # or pyproject.toml (approve deps first)
│   └── Dockerfile                 # if needed for Render
└── README.md
```

Clean Architecture mapping (backend):

| Layer | Folder | Responsibility |
|-------|--------|----------------|
| Interface | `api/` | HTTP, auth dependency, map errors |
| Application | `services/` | Use cases, validation rules, ownership |
| Domain/persistence | `models/` + `repositories/` | Entities + data access |
| Infrastructure | `storage/`, `core/` Supabase Auth client | External systems |

Routes never contain business logic. Repositories never call HTTP. Services never return raw ORM to the client without schema mapping.

---

## 2. Backend architecture

### 2.1 App bootstrap
- FastAPI app with CORS for frontend origin only
- Router mount: `/api/v1`
- Global exception handlers → API_CONTRACT error envelope
- Dependency: `get_current_user` / `get_workspace` from Bearer JWT (Supabase Auth validation)

### 2.2 Modules (services)
- `auth_service` — sign-up (Auth + profile + workspace), sign-in, sign-out, forgot/reset, me, change password
- `project_service` — CRUD, status transitions, soft-delete side effects
- `file_service` — limits, upload intent, confirm, download URL, delete + storage cleanup
- `resource_service` — CRUD (+ position)
- `progress_service` — CRUD, sort by `created_at DESC`
- `share_service` — enable (lazy row), disable, regenerate, public resolve
- `public_service` — aggregate public payload; public download URL

### 2.3 Cross-cutting
- Ownership helper: user → workspace → project (404 preferred for cross-tenant ids)
- Rate limiting on auth + public token routes (simple in-process or middleware; approve dependency if any)
- Config via env: Supabase URL, keys, JWT secret/jwks, storage bucket, frontend origin, signed URL TTL

### 2.4 What we will not build
No queues, microservices, websockets, search, or admin purge APIs.

---

## 3. Frontend architecture

### 3.1 Routing (matches UX)

| Route | Screen |
|-------|--------|
| `/` | Landing (redirect to `/projects` if session) |
| `/sign-up`, `/sign-in`, `/forgot-password`, `/reset-password` | Auth |
| `/projects` | Dashboard (`?status=` or client state for Active/Completed/Archived) |
| `/projects/[id]` | Workspace default Overview |
| `/projects/[id]/files` \| `resources` \| `progress` | Section tabs (or parallel routes / search params — prefer path segments for clarity) |
| `/settings` | Settings |
| `/p/[token]` | Public share |
| `not-found` | App 404; public unavailable uses dedicated UI on `/p/[token]` error |

### 3.2 Layering
- **Pages:** thin — compose features, pass params
- **Hooks:** data fetching/mutations per resource (`useProjects`, `useShare`, …)
- **`lib/api`:** one function per API_CONTRACT endpoint; typed models; envelope unwrap; map `error.code`
- **Components:** Harbor via shadcn theme tokens; no business logic in pure UI

### 3.3 Harbor implementation approach
- CSS variables for color/space/radius/motion from DESIGN_SYSTEM
- Tailwind theme extension mapped to those variables
- shadcn components restyled to Harbor (no pill primary buttons; border-led cards)
- Fonts: Satoshi + IBM Plex Mono (loading method approved in Milestone 0)
- Dark-only for V1

---

## 4. State management

Keep the smallest footprint (no Redux/Zustand unless later approved).

| Concern | Approach |
|---------|----------|
| Server state | React Query **or** Next.js fetch + local component state — **prefer TanStack Query only if approved**; otherwise native `useEffect`/SWR-free fetch wrappers in hooks for V1 |
| Auth session | Memory + `localStorage`/`sessionStorage` for access + refresh tokens; refresh on 401 once |
| UI ephemeral | Component state (dialogs, form fields, tab) |
| Toasts | Lightweight context or shadcn toast |
| No global project cache inventiveness | Invalidate/refetch after mutations |

**Recommendation to approve:** use **TanStack Query** for private app data (standard, small, matches DX). If you reject extra deps, use typed fetch hooks only.

Public page: single fetch of `GET /public/{token}` — no auth store.

---

## 5. Authentication flow

```
Sign-up:
  UI → POST /auth/sign-up
     → backend: Supabase Auth admin/signUp
     → insert users + workspaces
     → return user, workspace, session
     → FE stores tokens → /projects

Sign-in:
  UI → POST /auth/sign-in → session → /projects

Authenticated request:
  FE attaches Authorization: Bearer {access_token}
  BE validates JWT with Supabase → load users + workspace

Sign-out:
  POST /auth/sign-out → clear FE tokens → /sign-in

Forgot / Reset:
  POST /auth/forgot-password (always neutral success)
  Email link → /reset-password?token=... → POST /auth/reset-password

Settings:
  PATCH /auth/me (display_name)
  POST /auth/change-password
```

Clients never hit auth routes.

---

## 6. Storage flow

Per API_CONTRACT + DATA_MODEL:

```
Upload (owner):
  1. Validate name, mime, size, count (25 MiB, 50 files, allowlist)
  2. POST .../files/upload-url → upload_url + upload_token + expires_at
  3. Browser PUT/POST bytes to signed URL (not via API body)
  4. POST .../files/confirm → verify object → insert files row
  5. Response File model (never storage_path)

Download (owner):
  POST .../files/{id}/download-url → short-lived URL

Download (client):
  POST /public/{token}/files/{id}/download-url
  after share enabled + project not soft-deleted

Delete:
  Remove storage object + hard-delete DB row
  Compensate if one side fails (retry / ordered delete)
```

Bucket: private `project-files`.  
Key pattern: `{workspace_id}/{project_id}/{file_id}/{safe_filename}`.

---

## 7. Database layer

- SQLAlchemy models exactly matching DATA_MODEL entities:
  `users`, `workspaces`, `projects`, `files`, `resources`, `progress_entries`, `project_shares`
- Alembic migrations only
- Enums: `project_status`, `resource_type`
- Soft delete filter on project queries (`deleted_at IS NULL`)
- Unique: `users.email`, `workspaces.owner_user_id`, `files.storage_path`, `project_shares.project_id`, `project_shares.token`
- Indexes as specified in DATA_MODEL
- No RLS required in V1 if all access goes through backend (backend enforces tenancy). Optionally enable Supabase RLS later — **out of V1 unless you request**

---

## 8. API implementation order

Implement and verify against API_CONTRACT in this sequence:

1. **Foundation** — app, config, error envelope, health, CORS, DB session  
2. **Auth** — sign-up, sign-in, me, sign-out  
3. **Auth recovery** — forgot/reset, change-password, PATCH me  
4. **Projects** — list/create/get/patch/delete  
5. **Resources** — CRUD  
6. **Progress** — CRUD  
7. **Files** — list, upload-url, confirm, download-url, delete  
8. **Share private** — get/enable/disable/regenerate  
9. **Share public** — GET public aggregate, public download-url  
10. **Hardening** — rate limits, ownership edge cases, idempotent enable/disable  

Defer: `PUT /resources/order` unless UI needs it.

---

## 9. UI implementation order

Follow UX screens + Harbor; wire to real API only after each backend slice is ready (or mock behind `lib/api` with same types — prefer real API per milestone).

1. **Design tokens + base UI kit** (Button, Input, Dialog, Toast, Tabs, EmptyState)  
2. **Landing**  
3. **Auth screens**  
4. **App shell** (top bar, account menu) + **Dashboard** + Create Project modal  
5. **Project Workspace shell** (header, status, tabs, share cluster chrome)  
6. **Overview**  
7. **Resources**  
8. **Progress**  
9. **Files** (upload flow)  
10. **Share controls** (enable/copy/disable/regenerate + confirms)  
11. **Public page** + share unavailable  
12. **Settings**  
13. **404** + empty/loading/error polish + mobile public pass  

Owner tab order: Overview | Files | Resources | Progress.  
Public render order: Overview → Progress → Resources → Files.

---

## 10. Milestones

Each milestone: plan files → wait for approval → implement → verify → next.

### Milestone 0 — Monorepo scaffold
- Create `frontend/` and `backend/` skeletons
- Env templates (no secrets committed)
- Harbor token CSS + Tailwind wiring (minimal)
- FastAPI hello + error envelope stub
- **Deps to approve first:** Next, React, Tailwind, shadcn stack, Satoshi/Plex loading method, FastAPI, SQLAlchemy, Alembic, httpx/supabase client libs as needed

**Outcome:** Empty apps run locally; no product features yet.

### Milestone 1 — Database + Auth API
- Alembic: all tables from DATA_MODEL
- Auth endpoints + profile/workspace bootstrap
- Manual API test of sign-up → me

**Outcome:** Owner can register/login via API.

### Milestone 2 — Projects API + Dashboard UI
- Project CRUD/status/soft-delete API
- Auth UI + Dashboard + Create Project + session persistence

**Outcome:** Owner creates project and opens workspace shell (empty sections OK).

### Milestone 3 — Overview + Resources + Progress
- APIs + workspace sections UI end-to-end

**Outcome:** Owner edits overview; manages resources and progress timeline.

### Milestone 4 — Files + Storage
- Signed upload/download/delete
- Files UI with limits/errors

**Outcome:** Owner uploads and downloads files within limits.

### Milestone 5 — Share + Public page
- Share enable/disable/regenerate
- Public page + unavailable state + public download

**Outcome:** Full PRD happy path (owner share → client self-serve).

### Milestone 6 — Settings + polish
- Settings (name, password)
- Empty/loading/error states, confirms, a11y, mobile public QA
- Deploy pipeline notes (Vercel + Render)

**Outcome:** V1 release candidate matching success metrics.

---

## 11. Explicit non-goals during implementation

Do not implement: AI, chat, teams, billing, notifications, analytics, version history, comments, roles, client accounts, folders, search, password-protected shares, resource drag-reorder (unless approved), email verification wall, light theme.

---

## 12. Approval checkpoint

Please confirm:

1. **Approve this implementation plan** (structure, order, milestones).  
2. Resolve consistency defaults **A–E** above (or override).  
3. Approve **Milestone 0 dependency list** when we present it (fonts, shadcn, Supabase Python client, TanStack Query yes/no).

**No code will be written until you approve.**

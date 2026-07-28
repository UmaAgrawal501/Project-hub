# ProjectHub V2 — Product Requirements Document (PRD)

**Status:** Approved product specification (frozen for documentation alignment)  
**Audience:** Founders, product, design, engineering  
**Scope:** Product only — no architecture diagrams as implementation, no code  
**Relationship to V1:** V1 (“Client Project Workspace”) is feature-complete and frozen as history. V2 is a **product pivot** to a **Versioned Client Delivery Platform**. Public views are generated **only** from immutable published versions — **never** from draft data.

---

## 1. Product Overview

ProjectHub V2 is a SaaS **Versioned Client Delivery Platform** for freelancers, agencies, and independent creators.

Every engagement is a **Project**. The owner works in a private **Draft**, then **Publishes** an immutable **Version**. Each publish creates a **version-locked delivery link**; clients open that link and see **only that Version**.

ProjectHub is **not** a live collaborative workspace for clients, a task manager, a general drive, or a wiki. It is the permanent, versioned home for what was **delivered** to the client.

---

## 2. Product Identity

| | |
|---|---|
| **Category** | Versioned Client Delivery Platform |
| **Core Promise** | Draft. Publish. Deliver. Forever. |
| **Primary Value** | Clients always see a deliberate, immutable delivery — not your half-finished edits. |

**Philosophy:** We don't manage work. We deliver work.  
**V2 addendum:** We don't show work-in-progress to clients. We publish deliveries.

---

## 3. Problem Statement

V1 solved “one place for project files and links,” but a **live** shared workspace creates new problems:

- Clients see unfinished uploads and half-written notes.
- There is no record of what was delivered last week vs today.
- Regenerating confidence (“what did we actually send?”) is hard.
- Owners fear enabling the link until everything is “perfect,” delaying delivery.

Clients need a **published delivery**, not a peek into the owner’s desk.

---

## 4. Vision Statement

**Long term:** ProjectHub is the default way freelancers and agencies **publish** client deliveries — with clear versions, release notes, and a calm client portal.

**Version 2:** Nail the loop: edit Draft → Publish → immutable Version + delivery link → client sees that frozen publish → owner continues Draft → publish again (new link).

---

## 5. Target Users

**Primary (owners):** Freelancers, agencies, developers, designers, consultants.

**Secondary (recipients):** Clients who open a portal link.

Clients do **not** create accounts in V2. They view and download only.

---

## 6. Core Concepts (glossary)

| Concept | Definition |
|---------|------------|
| **Workspace** | Owner tenancy boundary (V2: one personal workspace per owner). |
| **Project** | Container for one client engagement: Draft + Versions + Share. Holds live lifecycle `status` and live `name` for the owner. |
| **Draft** | Private, mutable working copy (overview, files, resources). Never visible on the Client Portal. |
| **Publish** | Explicit action that freezes Draft content **and the current project name** into a new immutable Version. |
| **Version** | Immutable snapshot at publish time: project name, overview, files, resources, release notes, version number, published_at. |
| **Release Notes** | Owner-authored summary attached to a Version explaining what changed in that delivery. |
| **Files** | Delivery documents (in Draft while editing; snapshotted into each Version). |
| **Resources** | Typed permanent links (same Draft / Version split). |
| **Client Portal** | Public, read-only destination for a share token; content = published Versions only. |
| **Share** | Per-version delivery link for the portal (minted on publish; disable / regenerate latest). |

**Overview** lives on the Draft and is copied into each Version at publish. The portal overview always comes from the selected Version — never from Draft.

**Progress (V1)** is **removed**. Delivery narrative is **Release Notes** per Version.

### Project name vs lifecycle status

| Field | Live on Project? | Snapshotted into Version? | Portal source |
|-------|------------------|---------------------------|---------------|
| **name** | Yes (owner edits anytime) | **Yes** — copied at Publish | **Version snapshot only** |
| **status** (`active` / `completed` / `archived`) | Yes | **No** | **Live project row** |

Renaming a project after publish does **not** change names shown for existing Versions until the owner publishes again. Changing status updates the portal immediately without a new publish.

### Active / Completed / Archived

Owner project lifecycle statuses. Orthogonal to versioning (e.g. Active + Version 3 is valid).

| Status | Owner meaning | Portal when share enabled + ≥1 Version |
|--------|---------------|----------------------------------------|
| `active` | In progress | Accessible |
| `completed` | Finished engagement | **Accessible** |
| `archived` | Shelved from Active filter | **Accessible** |

**Only soft-delete** removes portal access (along with disabled/invalid share or never published).

---

## 7. User Journey

### Owner

1. Sign up / sign in → Dashboard.  
2. Create Project → empty Draft (unpublished).  
3. Edit Draft: name, overview, files, resources.  
4. Publish → must supply Release Notes → creates **Version N** (immutable), including snapshotted **name**, and a **new delivery link** locked to Version N.  
5. Copy that portal link to the client.  
6. Continue editing Draft (clients with the vN link still see only Version N).  
7. Publish again → Version N+1 + **new** delivery link; the previous link remains valid and still shows only Version N.  
8. Optionally browse Version History (and copy each version’s link); optionally complete/archive; optionally soft-delete project.

### Client

1. Open a portal delivery link (no login).  
2. See **only the Version locked to that link** (name from that Version, live status, release notes, overview, resources, files).  
3. Download files / open resource links for that Version.  
4. If that share is disabled, token invalid, project soft-deleted, or the locked Version is missing → unavailable state.

---

## 8. Core Features

### Authentication

Owner accounts only. Sessions private. Surfaces: sign-up, sign-in, sign-out, settings (display name / password), forgot-password, reset-password.

### Dashboard

List projects with lifecycle filters (Active / Completed / Archived). Soft-deleted projects are excluded.

**Delivery badges (normative):**

| Condition | Badges shown |
|-----------|--------------|
| `latest_version_number` is null | **Not published** only |
| `latest_version_number` is N and Draft equals latest Version | **vN** only |
| `latest_version_number` is N and Draft differs from latest Version | **vN** and **Unpublished changes** |

**Dirty / unpublished changes (normative):**

- `latest_version_number == null` → **Not published**. This state is **not** dirty. `has_unpublished_changes` is **false**.  
- `latest_version_number != null` and Draft differs from that Version → **Unpublished changes**. `has_unpublished_changes` is **true**.  
- `latest_version_number != null` and Draft matches that Version → not dirty. `has_unpublished_changes` is **false**.

### Projects

- Belong to owner workspace.  
- Live `name` (1–120 chars after trim) + live lifecycle `status`.  
- Creating a project creates an empty Draft; **no Version** until first Publish.  
- Soft-delete sets `deleted_at`, removes the project from owner lists, disables **all** shares, and kills portal access. Soft-delete is a **supported V2 owner action** (confirm in UX).

### Draft (private)

Mutable:

- Overview (description)  
- Files  
- Resources  

Rules:

- Only the authenticated owner can read/write Draft.  
- Draft is never returned by public APIs.  
- After publish, Draft remains editable and may diverge from the latest Version (“unpublished changes”).

### Publish

- Explicit owner action.  
- Requires Release Notes (non-empty after trim; 1–10_000 characters).  
- Creates the next Version number (monotonic per project, starting at 1).  
- Snapshots into the Version: **project name** (current live name), Draft overview, Draft files, Draft resources, release notes.  
- Version content is **immutable** after creation (no edit, no delete of version content in V2).  
- Publishing requires a non-empty Draft: at least one of (a) overview with length > 0 after trim, (b) ≥1 draft file, (c) ≥1 draft resource. Otherwise reject.  
- Republishing an unchanged Draft with new release notes is **allowed** (creates a new Version).

### Versions

- Ordered by `version_number` ascending historically; **latest** = highest number.  
- Owner and public list endpoints return versions with **highest number first** (descending).  
- Each Version includes: `version_number`, `published_at`, `release_notes`, snapshotted `name`, snapshotted `overview`, files snapshot, resources snapshot.  
- Owner can list and view any Version and copy that Version’s delivery link.  
- Each client link is locked to one Version; opening an older link does not expose newer Versions.

### Files

- Draft: upload / download / delete (owner).  
- Version: download only (owner and client via portal).  
- Limits (normative — see API Contract): max **25 MiB** per file; max **50** draft files per project; MIME allowlist as in API Contract.  
- Published file bytes must remain readable for that Version even if Draft later deletes or replaces the draft file. **Storage rule:** on publish, copy each draft file object into a distinct immutable version key namespace (copy-on-publish). Draft and version objects never share a mutable path.

### Resources

- Draft: add / edit / delete typed links.  
- Version: open links read-only as snapshotted.  
- Types: closed enum (see Data Model).  
- Limits: title 1–120; URL http(s) ≤2048; description optional ≤2000; position ≥0.

### Release Notes

- Required on Publish (1–10_000 chars after trim).  
- Shown on the Client Portal for the selected Version.  
- Immutable with the Version.

### Share & Client Portal

- **One share row per published Version** (unique `(project_id, version_number)`); minted on Publish with a new token.  
- Portal requires **all** of: valid token, that share enabled, project `deleted_at` is null, **and** the share’s `version_number` exists.  
- `active`, `completed`, and `archived` projects remain portal-accessible when the above hold.  
- Portal **never** reads Draft.  
- Portal **name** always comes from the **locked Version snapshot**.  
- Portal **status** always comes from the **live project** row.  
- Portal content is **only** the locked Version (no version switcher on that token).  
- Owner disable kills **all** delivery links for the project; regenerate rotates only the **latest** Version’s token (older links unchanged).

### Settings

Display name (1–80), change password, sign out, read-only email. Forgot/reset password supported as product surfaces.

### Soft delete

Owner may soft-delete a project (destructive confirm). Effect: removed from Dashboard lists; all shares disabled; all public portal access returns unavailable. Versions and draft data are retained for the soft-deleted row in V2 (no purge product requirement in V2).

---

## 9. Explicit Non-Goals (V2)

- Client accounts  
- Editing or deleting published Versions  
- Auto-publish / scheduled publish  
- Diff UI between versions (list + view is enough)  
- Restore Version → Draft (may be later)  
- Teams / roles / comments / notifications  
- AI, billing, analytics, search  
- Password-protected shares  
- Folders / nested file trees  
- Live “Progress” timeline (replaced by Release Notes)  
- Light mode (Harbor dark-first remains unless Design System says otherwise)  
- Showing Draft on any public surface  
- Versioning of project `status`  

---

## 10. Success Metrics (qualitative V2)

- Owner can publish Version 1 and share without fear of live edits leaking.  
- Client always sees a complete, intentional delivery.  
- Owner can publish Version 2+ while Draft remains private.  
- “What did we deliver on date X?” answered via Version History / portal prior versions.  
- Renaming after publish does not rewrite historical Version names until a new publish.

---

## 11. Validation limits (normative)

| Field | Limit |
|-------|-------|
| Project `name` | Required; 1–120 characters after trim |
| Draft / Version `overview` | Optional; null or 0–10_000 characters after trim. Empty string after trim is stored/treated as null for publish emptiness checks |
| `release_notes` | Required on publish; 1–10_000 characters after trim |
| User `display_name` | 1–80 characters after trim |
| Draft file size | ≤ 25 MiB |
| Draft files per project | ≤ 50 |
| Resource `title` | 1–120 |
| Resource `url` | http or https; ≤ 2048 |
| Resource `description` | Optional; ≤ 2000 |
| New password | ≥ 8 characters (existing auth rules) |

MIME allowlist: see API Contract.

---

## 12. Document set (V2)

| Doc | Role |
|-----|------|
| `docs/v2/PRD.md` | Product source of truth (this file) |
| `docs/v2/UX.md` | Screens and flows |
| `docs/v2/DATA_MODEL.md` | Conceptual entities |
| `docs/v2/API_CONTRACT.md` | HTTP API |

**Harbor Design System** (`docs/DESIGN_SYSTEM.md`) remains the visual language until a V2 design delta is approved; product behavior is governed by this V2 set.

**Implementation is frozen** until engineering is explicitly unblocked after this documentation set is signed off.

---

## 13. Approval checkpoint

This PRD is the product source of truth for V2. UX, Data Model, and API Contract must stay aligned with it. No V2 application code until engineering kickoff is approved.

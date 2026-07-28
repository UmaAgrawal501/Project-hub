# ProjectHub V2 — UX Specification

**Status:** Approved UX specification (aligned with V2 PRD)  
**Depends on:** `docs/v2/PRD.md`  
**Scope:** Screens, flows, hierarchy, empty/error states — no visual tokens (see Harbor Design System), no code  
**Hard rule:** Client Portal content is **always** from immutable published Versions. Draft is owner-only.  
**Visual language:** Harbor (`docs/DESIGN_SYSTEM.md`) until a V2 design delta is approved.

---

## 1. Navigation map

### Owner (authenticated)

```
Sign in / Sign up
  └── Dashboard
        ├── Create Project → Draft (Overview)
        ├── Open Project → Draft shell
        │     ├── Overview (Draft)
        │     ├── Files (Draft)
        │     ├── Resources (Draft)
        │     ├── Publish
        │     ├── Version History
        │     ├── Share controls
        │     └── Delete project (destructive)
        ├── Forgot / Reset password (unauthenticated entry points)
        └── Settings
```

### Client (unauthenticated)

```
/p/{token}
  ├── Latest Version (default)
  ├── Prior Version (select)
  └── Unavailable
```

---

## 2. Auth

**Sign up / Sign in** — Minimal friction into Dashboard. Inline validation; no browser alerts.  
**Forgot password** — Email entry → success state that does not reveal whether the email exists (same calm confirmation either way).  
**Reset password** — Tokenized link entry → set new password (≥8) → sign in.  
**Settings** — Display name (1–80), change password, email read-only, sign out.  
**Empty / Error** — Inline validation; no browser alerts.

---

## 3. Dashboard

**Purpose:** Find projects and see delivery state at a glance.

**Actions:** Create project; open project; filter Active | Completed | Archived.

**Row information (priority):**
1. Project name (live)  
2. Lifecycle status pill (`active` / `completed` / `archived`)  
3. Delivery badges — see matrix below  
4. Updated time  

**Delivery badge matrix (normative):**

| Condition | Badges |
|-----------|--------|
| Never published (`latest_version_number` null) | `Not published` |
| Published, Draft matches latest Version | `vN` |
| Published, Draft differs from latest Version | `vN` **and** `Unpublished changes` |

Never published is **not** shown as Unpublished changes.

**Empty:** First-project coaching + Create CTA.  
**Filtered empty:** Calm message + switch filter. Soft-deleted projects never appear.

---

## 4. Create Project

**Fields:** Name (required, 1–120); optional overview seed for Draft (≤10_000).  
**Result:** Project + empty Draft; **no Version**; navigate to Draft Overview.  
**Not a wizard.**

---

## 5. Draft shell (Project Workspace)

**Purpose:** Private editing surface. Never shown to clients.

**Chrome:**
1. Back to Dashboard  
2. Project name (live) + lifecycle status (live)  
3. Delivery strip:
   - If never published: `Not published`
   - If published: `Version N` (latest) plus `Unpublished changes` when dirty  
4. Primary: **Publish**  
5. After publish: show / copy the **new delivery link** for that Version  
6. Nav: Files | Versions | Delete project  

**Notes:**
- Delivery links are created on Publish (not before).  
- Each Version has its own link; older links stay locked to that Version.  
- Completed and Archived projects open the same editor; links remain usable until disabled or soft-deleted.

---

## 6. Draft — Overview

**Actions:**
- Edit **name** (project live field)  
- Edit **overview** (Draft)  
- Change **lifecycle status** (Active / Completed / Archived)  
- Save  

**Save mapping:** Persist name/status via project update; persist overview via draft update (two API calls is fine; one Save control in UI).  

**Empty overview:** Prompt to add a client-facing description (still private until publish).  
**Success:** Saved; apply dirty rules from PRD (name change vs snapshotted Version name counts as unpublished changes when a Version exists).

---

## 7. Draft — Files

**Actions:** Upload, download, delete (confirm).  
**List:** Name, size, date, actions.  
**Empty:** “Upload the documents for your next delivery” + Upload.  
**Errors:** Type/size/limit (25 MiB, 50 files, MIME allowlist) inline; no alerts.  
**Note:** Deleting a Draft file does not alter published Versions.

---

## 8. Draft — Resources

**Actions:** Add, edit, delete (confirm); open URL.  
**Fields:** Title (1–120), URL (http/https ≤2048), type (enum), optional description (≤2000).  
**Empty:** “Add GitHub, Figma, production URL…” + Add.

---

## 9. Publish

**Purpose:** Create the next immutable Version from current Draft (and current project name).

**Entry:** Publish button in Draft shell (and empty-state CTA on History when never published).

**Pre-validation (disable or block with explanation):**
- Nothing to publish (no trimmed overview, no files, no resources)  
- Empty release notes  

**Flow:**
1. Confirm panel: summarizes what will be frozen (project name that will be snapshotted; overview present/absent; counts of files/resources).  
2. **Release notes** required (1–10_000 after trim).  
3. Confirm Publish → success → Version N + delivery link created; dirty indicator clears if Draft still matches; toast “Published Version N — new link ready”.  
4. Stay on editor after success; show the new link to copy.

**Errors:** Nothing to publish; empty release notes; conflict/network with retry.  

**Allowed:** Republish identical Draft content with new release notes.  

**Non-goals:** Schedule, partial publish, edit after publish.

---

## 10. Version History (owner)

**Purpose:** Audit what was delivered.

**List:** Version number (highest first), published date, release notes excerpt, snapshotted name (optional secondary line), **delivery link** (copy).  
**Open Version:** Read-only view matching portal delivery hierarchy for that Version:
1. Snapshotted name (as delivered)  
2. Version label · published date  
3. Release notes  
4. Overview  
5. Resources  
6. Files (download)  

Live lifecycle status may appear in owner chrome only; it is not part of the immutable delivery body.  

**Empty:** “Publish your first delivery” + Publish CTA.

---

## 11. Share controls

**Actions:** Copy link for the current/latest publish; list prior version links in Versions; Disable all (confirm); Regenerate latest (confirm — only that version’s old URL dies).  
**Copy:** Clipboard + toast.  
**Messaging:** “Each publish creates a new link. Older links stay on that version only.”

**States:**

| Condition | Portal behavior | Owner messaging |
|-----------|-----------------|-----------------|
| Share off / bad token / soft-deleted project | Unavailable | — |
| Never published | No delivery link yet | Publish to create a link |
| Share on for a Version, any of Active/Completed/Archived | Portal loads **that** Version only | — |

Completed and Archived remain shareable. Soft-delete disables all links (plus per-project disable / regenerate-latest / invalid token).

---

## 12. Client Portal

**Purpose:** Read-only delivery destination for one frozen Version.

**No** owner chrome, auth, or Draft affordances.

**Default:** The Version locked to the token (only version available on that link).

**Hierarchy:**
1. **Project name** — always from the **locked Version snapshot** (never live `projects.name`)  
2. **Lifecycle status** — always from the **live project** (`active` / `completed` / `archived`)  
3. Version label (`Version N` · published date)  
4. Release notes  
5. Overview  
6. Resources  
7. Files (download)

**Recommended order of body sections:** Release notes → Overview → Resources → Files.

**Empty sections:** Hide empty sections on portal.  
**No version switcher** on a delivery link (token is version-locked).  
**Download failure:** Inline retry.  
**Unavailable:** “This link is no longer active” + short explanation; optional “Contact the project owner.” Do not leak Draft existence, status, or whether the project was deleted vs unpublished.

---

## 13. Delete project

**Supported in V2.** Soft-delete only.

**Entry:** Danger zone in Draft shell (and optionally from Dashboard overflow — Draft shell is required).  

**Flow:**
1. Destructive confirm naming the project.  
2. Explain: removed from Dashboard; client link stops working; this cannot be undone in V2 UI.  
3. Confirm → soft-delete → return to Dashboard Active filter.  

**Not shown:** Hard delete. No restore UI in V2.

---

## 14. Empty states (system)

| Surface | Intent | CTA |
|---------|--------|-----|
| Dashboard none | First project | Create project |
| Draft files | Prepare delivery docs | Upload |
| Draft resources | Pin links | Add resource |
| History none | First publish | Publish |
| Portal section empty | Hide section | — |
| Archived filter empty | Nothing archived | Back to Active |
| Completed filter empty | Nothing completed | Back to Active |

---

## 15. Accessibility & mobile (product rules)

- Keyboard-complete owner flows including Publish, Share, and Delete.  
- Dialogs: focus trap; Escape closes non-destructive; destructive confirms require explicit action.  
- Toasts: `aria-live`.  
- Portal: mobile-first; hit targets ≥ 44px for Download / Open; no hover-only actions.  
- One `h1` on portal = Version snapshotted project name.

---

## 16. Out of UX scope (V2)

Diff views, restore-to-draft, client comments, password gate, Progress timeline, drag-and-drop uploads (default **button upload**).

---

## 17. Approval checkpoint

This UX is aligned with the V2 PRD. No implementation until engineering kickoff is approved.

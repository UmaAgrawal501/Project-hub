# ProjectHub — UX Design (Version 1)

**Status:** Draft for review  
**Audience:** Founders, product, design, engineering  
**Scope:** Experience only — no visual design, no implementation  
**Product SSOT:** `docs/PRD.md` (frozen — do not modify)

This document defines every screen, state, and navigation path for ProjectHub V1.

**Design north star:** Linear clarity, Notion calm, Vercel speed, GitHub information hierarchy.  
**Product law:** Overview · Files · Resources · Progress — fewest clicks possible.

---

## Global UX Rules

- Dark-mode-first, but this document does not specify colors.
- Owner app and public share page are different experiences (chrome vs no chrome).
- Destructive actions always confirm (delete file, disable share, regenerate link, archive).
- Primary actions are obvious; secondary actions are quiet.
- Every list supports scanability: name first, metadata second, actions last.
- Mobile: public page is phone-first; owner app is desktop-first but usable on tablet.

### Actors

| Actor | Auth | Can |
|-------|------|-----|
| Owner | Yes | Create/manage projects, upload, share |
| Client | No | View/download via share link only |

---

# Screens

## 1. Landing Page

**Purpose:** Explain ProjectHub in one viewport and convert visitors to sign up.  
**Primary user:** Prospective owner (freelancer / agency).  
**User goal:** Understand “One Project. One Workspace. One Link.” and create an account.

**Actions available**
- Sign up (primary)
- Log in (secondary)
- Optional: jump to short “How it works” section on the same page

**Information hierarchy**
1. Product name + core promise  
2. One supporting sentence (never resend files)  
3. CTA group  
4. Minimal how-it-works (3 steps max)  
5. Footer (legal links later; V1 can be sparse)

**Empty / Success / Error**
- Empty: N/A (marketing page).  
- Success: CTA click → Authentication.  
- Error: N/A on page itself.

**Notes:** No dashboard chrome. No feature grid. No stats strip. Brand and promise first.

---

## 2. Authentication

Screens: **Sign up**, **Sign in**, **Forgot password**, **Reset password**.

**Purpose:** Let owners access their private workspace securely.  
**Primary user:** Owner.  
**User goal:** Get into the dashboard with minimal friction.

### Sign up
**Actions:** Enter name, email, password → Create account → (optional verify email if product requires it) → Dashboard.  
**Hierarchy:** Title → form → submit → link to Sign in.  
**Empty:** Blank form with clear labels.  
**Success:** Account created → Dashboard (or verify-email interstitial if required).  
**Error:** Invalid email, weak password, email already used — inline field errors.

### Sign in
**Actions:** Email + password → Sign in; link to Forgot password; link to Sign up.  
**Hierarchy:** Title → form → submit → helper links.  
**Empty:** Blank form.  
**Success:** Dashboard.  
**Error:** Invalid credentials (generic message — do not reveal which field failed).

### Forgot / Reset password
**Actions:** Request reset email → open link → set new password → Sign in.  
**Success:** Confirmation that email was sent / password updated.  
**Error:** Unknown email (still show neutral success to avoid enumeration, or soft message per security preference — prefer neutral).  
**Empty:** Email field only / new password fields.

**Notes:** Clients never see these screens.

---

## 3. Dashboard

**Purpose:** Home for all Active and Completed projects; entry to create and open workspaces.  
**Primary user:** Owner.  
**User goal:** Find a project quickly or start a new one.

**Actions available**
- Create project (primary)
- Open project
- Filter / segment: Active | Completed | (Archived via secondary entry)
- Change status from row menu (optional V1: open project to change status)
- Sign out / open Settings (via account menu)

**Information hierarchy**
1. App shell: ProjectHub mark, account menu  
2. Page title “Projects” + Create  
3. Status tabs/filters: Active (default), Completed, Archived  
4. Project list: Name → Status → Updated → optional short overview snippet  

**Empty state**
- First visit: “Create your first project” + short line on One Link for clients + Create CTA.  
- Filtered empty (e.g. no Completed): calm message + switch filter / create.

**Success state**
- List populated; create opens Create Project; row opens Project Workspace.

**Error state**
- Failed to load projects: retry.  
- Failed create (handled on Create Project).

---

## 4. Create Project

**Purpose:** Create a project in the fewest steps.  
**Primary user:** Owner.  
**User goal:** Name the project and land inside its workspace.

**Actions available**
- Enter name (required)
- Enter overview / description (optional)
- Create → open Project Workspace (Overview)
- Cancel / dismiss

**Information hierarchy**
1. Title “New project”  
2. Name field  
3. Overview field  
4. Create (primary) / Cancel  

**Empty state:** Blank form, name focused.  
**Success state:** Project created as **Active** → navigate to Project Workspace.  
**Error state:** Missing name; generic create failure with retry.

**Notes:** Prefer modal or focused panel from Dashboard (Linear-style), not a multi-step wizard.

---

## 5. Project Workspace (Shell)

**Purpose:** Frame for one project; persistent navigation across Overview, Files, Resources, Progress, and Share.  
**Primary user:** Owner.  
**User goal:** Move between sections without losing project context; manage sharing and status.

**Actions available**
- Navigate sections: Overview | Files | Resources | Progress  
- Back to Dashboard  
- Share controls: Enable / Disable / Copy link / Regenerate  
- Change status: Active | Completed | Archived  
- Account menu / Settings  

**Information hierarchy**
1. Back + Project name + Status  
2. Share control cluster (always reachable)  
3. Section navigation  
4. Section content  

**Empty / Success / Error:** Shell itself always has project context; section states live in child screens.  
**Error:** Project not found / soft-deleted → 404 or “Project unavailable.”

**Notes:** Share is a first-class control, not buried in Settings. This is the delivery product’s climax action.

---

## 6. Overview

**Purpose:** Answer “What is this project?”  
**Primary user:** Owner (edit); Client sees read-only equivalent on Public page.  
**User goal:** Understand or edit the project’s identity.

**Actions available (owner)**
- Edit name  
- Edit overview / description  
- Change status  
- Save (explicit or autosave with clear saved indicator — prefer explicit Save for V1 clarity)

**Information hierarchy**
1. Project name  
2. Status  
3. Overview body  
4. Lightweight meta: created / last updated (secondary)

**Empty state:** Overview blank — prompt “Add a short description for your client.”  
**Success state:** Saved confirmation (subtle).  
**Error state:** Save failed; validation (name required).

---

## 7. Files

**Purpose:** Answer “Where are all important files?”  
**Primary user:** Owner (manage); Client (download on public page).  
**User goal:** Upload curated delivery documents; find and download them fast.

**Actions available (owner)**
- Upload file(s)  
- Download  
- Delete (confirm)  
- View name, size, date  

**Information hierarchy**
1. Section title + Upload  
2. File list: Name → Size → Uploaded date → actions  

**Empty state:** “Upload the documents your client will need” + Upload CTA. No fake folders.  
**Success state:** File appears in list after upload; download works.  
**Error state:** Type/size rejected; upload failed; delete failed — inline or toast with retry.

**Notes:** Flat list only. No nested folders in V1.

---

## 8. Resources

**Purpose:** Answer “Where are all important links?”  
**Primary user:** Owner (manage); Client (open links).  
**User goal:** Keep permanent project URLs one click away.

**Actions available (owner)**
- Add resource  
- Edit resource  
- Delete resource (confirm)  
- Open URL  

**Fields:** Title, URL, Type, optional description.

**Information hierarchy**
1. Section title + Add  
2. List: Type indicator → Title → URL/description → actions  

**Empty state:** “Add GitHub, Figma, production URL…” + Add CTA.  
**Success state:** Resource in list; open works in new tab.  
**Error state:** Invalid URL; missing title; save/delete failure.

---

## 9. Progress

**Purpose:** Answer “What changed recently?” / “What’s the latest?”  
**Primary user:** Owner (post); Client (read).  
**User goal:** Publish and scan a client-facing timeline.

**Actions available (owner)**
- Add progress entry (title + description)  
- Edit / Delete entry (confirm delete)  

**Information hierarchy**
1. Section title + Add  
2. Timeline newest-first: Date → Title → Description  

**Empty state:** “Post your first progress update for the client” + Add CTA.  
**Success state:** New entry at top of timeline.  
**Error state:** Missing title; save/delete failure.

---

## 10. Public Share Page

**Purpose:** Client-facing read-only project destination.  
**Primary user:** Client.  
**User goal:** Understand the project and get files/links/latest progress without contacting the owner.

**Actions available**
- Read Overview  
- Open Resources  
- Download Files  
- Read Progress  
- No edit, upload, delete, or account UI  

**Information hierarchy**
1. Project name + status (read-only)  
2. Overview  
3. Progress (often checked first for “what’s new” — place high; after overview or adjacent)  
4. Resources  
5. Files  

Recommended public order for scan: **Overview → Progress → Resources → Files** (delivery narrative). Owner app may keep nav order Overview | Files | Resources | Progress to match PRD mental model; public page prioritizes “what’s new” earlier.

**Empty states (section-level):** Hide empty sections or show quiet “No files yet” — prefer hide empty sections on public page to reduce noise.  
**Success state:** Page loads; downloads and outbound links work.  
**Error state:**
- Invalid / disabled / regenerated token → dedicated unavailable page (“This link is no longer active”).  
- Download failure → retry message.

**Notes:** No owner dashboard chrome. Mobile-first. Feels like a status page, not a file dump.

---

## 11. Settings

**Purpose:** Minimal account control. Keep tiny for V1.  
**Primary user:** Owner.  
**User goal:** Update profile/security and sign out cleanly.

**Actions available**
- Edit display name  
- Change password  
- View email (read-only in V1 unless change-email is trivial)  
- Sign out  
- Optional: open Archived projects shortcut if not on Dashboard  

**Information hierarchy**
1. Account  
2. Security  
3. Sign out  

**Empty state:** N/A.  
**Success state:** Saved / password updated.  
**Error state:** Validation; save failure.

**Out of Settings for V1:** Billing, team, notifications, API keys, themes beyond product default.

---

## 12. 404 / Unavailable

**Purpose:** Honest recovery when a route or share link is invalid.  
**Primary user:** Owner or Client.  
**User goal:** Understand failure and get back somewhere useful.

### App 404 (owner, logged in)
**Actions:** Go to Dashboard.  
**Hierarchy:** Message → Dashboard CTA.  
**Empty/Success:** N/A.  
**Error:** This screen *is* the error state — calm, not alarming.

### Share unavailable (client)
**Actions:** None required; optional “Contact the project owner.”  
**Hierarchy:** “This link is no longer active” → short explanation (disabled or regenerated).  
**Do not** expose whether the project exists internally beyond that.

---

## 13. Empty States (System)

Empty states are first-run coaching, not dead ends.

| Surface | Message intent | Primary CTA |
|---------|----------------|-------------|
| Dashboard (no projects) | Create first project home | Create project |
| Files | Curate client documents | Upload |
| Resources | Pin permanent links | Add resource |
| Progress | Tell the client what’s latest | Add progress |
| Public (section empty) | Prefer hide section | — |
| Archived filter empty | Nothing archived | Back to Active |

Tone: short, confident, no humor clutter, no multi-paragraph onboarding tours in V1.

---

# Navigation Flow

## Owner (authenticated)

```
Landing
  ├─ Sign up ─────────────────────────────► Dashboard
  └─ Sign in ─────────────────────────────► Dashboard
        │
        ├─ Forgot password → Reset → Sign in
        │
Dashboard
  ├─ Create Project ──────────────────────► Project Workspace (Overview)
  ├─ Open Project ────────────────────────► Project Workspace
  ├─ Settings ◄───────────────────────────► Dashboard
  └─ Sign out ────────────────────────────► Sign in

Project Workspace
  ├─ Overview
  ├─ Files
  ├─ Resources
  ├─ Progress
  ├─ Share: Enable | Copy | Disable | Regenerate
  ├─ Status: Active | Completed | Archived
  └─ Back ────────────────────────────────► Dashboard
```

## Client (unauthenticated)

```
Share Link
  ├─ Valid + enabled ─────────────────────► Public Share Page
  │                                            ├─ Overview (read)
  │                                            ├─ Progress (read)
  │                                            ├─ Resources (open)
  │                                            └─ Files (download)
  └─ Invalid / disabled / regenerated ────► Share Unavailable
```

## Cross-cutting

- Logged-in owner hitting `/` marketing may redirect to Dashboard (product choice: prefer redirect after auth).  
- Logged-out user hitting Dashboard → Sign in.  
- Unknown app routes → App 404.

---

# Share Control UX (Detail)

Always available in Project Workspace header.

| State | Owner sees | Client link |
|-------|------------|-------------|
| Sharing off | Enable sharing | Dead |
| Sharing on | Copy link, Disable, Regenerate | Works |
| After regenerate | New link; warning that old link dies | Old dead, new works |
| After disable | Enable again | Dead |

Regenerate and Disable require confirmation: “Anyone with the old link will lose access.”

---

# Low-Fidelity Wireframes (ASCII)

## Landing

```
+--------------------------------------------------+
| ProjectHub                          Log in  Sign up |
|--------------------------------------------------|
|                                                  |
|   ProjectHub                                     |
|   One Project. One Workspace. One Link.          |
|                                                  |
|   Never resend project files again.              |
|                                                  |
|   [ Create free account ]                        |
|                                                  |
|   1. Create project                              |
|   2. Add files, resources, progress              |
|   3. Share one link with your client             |
|                                                  |
+--------------------------------------------------+
```

## Sign in / Sign up

```
+----------------------------------+
| ProjectHub                       |
| Sign in                          |
|                                  |
| Email    [____________________]  |
| Password [____________________]  |
|                                  |
| [ Sign in ]                      |
| Forgot password?  ·  Sign up     |
+----------------------------------+
```

## Dashboard

```
+--------------------------------------------------+
| ProjectHub                    [Account ▾]        |
|--------------------------------------------------|
| Projects                        [ + New project ]|
| Active | Completed | Archived                    |
|--------------------------------------------------|
| Name                    Status      Updated      |
| Acme Website Redesign   Active      2h ago     > |
| Northwind Mobile App    Active      Yesterday  > |
| Contoso API             Completed   Mar 12     > |
+--------------------------------------------------+

Empty:
| Projects                        [ + New project ]|
| Create your first project                        |
| One home for files, links, and progress.         |
| [ Create project ]                               |
```

## Create Project

```
+----------------------------------+
| New project                    X |
|----------------------------------|
| Name *                           |
| [______________________________] |
| Overview                         |
| [______________________________] |
| [______________________________] |
|                                  |
| [ Cancel ]        [ Create ]     |
+----------------------------------+
```

## Project Workspace Shell + Overview

```
+--------------------------------------------------+
| <- Projects                                      |
| Acme Website Redesign          Status [Active ▾] |
| Sharing: Off  [ Enable sharing ]                 |
|--------------------------------------------------|
| Overview | Files | Resources | Progress          |
|--------------------------------------------------|
| Overview                                         |
| Name                                             |
| [ Acme Website Redesign                      ]   |
| Description                                      |
| [ Client site rebuild · Q2 delivery          ]   |
| [                                            ]   |
|                          [ Save ]                |
+--------------------------------------------------+

Sharing on:
| Sharing: On  [ Copy link ] [ Disable ] [ Regenerate ] |
```

## Files

```
| Overview | Files | Resources | Progress          |
|--------------------------------------------------|
| Files                           [ Upload ]       |
|--------------------------------------------------|
| Proposal.pdf           240 KB    Mar 01   ⬇  🗑  |
| Contract.pdf           110 KB    Mar 02   ⬇  🗑  |
| Brand-assets.zip       4.2 MB    Mar 10   ⬇  🗑  |
+--------------------------------------------------+

Empty:
| No files yet                                     |
| Upload the documents your client will need.      |
| [ Upload ]                                       |
```

## Resources

```
| Resources                        [ + Add ]       |
|--------------------------------------------------|
| Figma     Design file                            |
|           https://figma.com/...          Open  … |
| GitHub    Repository                             |
|           https://github.com/...         Open  … |
| Prod      Production URL                         |
|           https://acme.com               Open  … |
+--------------------------------------------------+

Add / Edit resource:
| Title [________]  Type [ Figma ▾ ]               |
| URL   [________________________________]         |
| Description (optional)                           |
| [ Cancel ]                    [ Save ]           |
```

## Progress

```
| Progress                         [ + Add ]       |
|--------------------------------------------------|
| Mar 18                                           |
| Deployment completed                             |
| Staging promoted to production.                  |
|--------------------------------------------------|
| Mar 12                                           |
| Authentication module completed                  |
| Login and password reset shipped.                |
+--------------------------------------------------+

Empty:
| No progress yet                                  |
| Post an update so clients know what’s latest.    |
| [ Add progress ]                                 |
```

## Public Share Page (Client)

```
+--------------------------------------------------+
| Acme Website Redesign              Status: Active|
|--------------------------------------------------|
| Overview                                         |
| Client site rebuild · Q2 delivery                |
|--------------------------------------------------|
| Progress                                         |
| Mar 18 · Deployment completed                    |
| Mar 12 · Authentication module completed         |
|--------------------------------------------------|
| Resources                                        |
| Figma · Design file                         Open |
| Prod  · Production URL                      Open |
|--------------------------------------------------|
| Files                                            |
| Proposal.pdf                               ⬇     |
| Contract.pdf                               ⬇     |
+--------------------------------------------------+
```

## Share Unavailable

```
+----------------------------------+
| This link is no longer active    |
|                                  |
| The owner disabled or replaced   |
| this share link.                 |
| Contact them for a new link.     |
+----------------------------------+
```

## Settings

```
+--------------------------------------------------+
| <- Back                                          |
| Settings                                         |
|--------------------------------------------------|
| Account                                          |
| Name  [________________]                         |
| Email  you@studio.com                            |
|                                                  |
| Security                                         |
| [ Change password ]                              |
|                                                  |
| [ Sign out ]                                     |
+--------------------------------------------------+
```

## App 404

```
+----------------------------------+
| Page not found                   |
|                                  |
| [ Go to projects ]               |
+----------------------------------+
```

---

# UX Acceptance Checklist (V1)

- [ ] Owner can go from empty Dashboard → shared link in under 2 minutes without confusion.  
- [ ] Share enable/copy is one obvious control in the project shell.  
- [ ] Client public page answers all four product questions without an account.  
- [ ] Disable/Regenerate clearly kills old access.  
- [ ] Empty states teach the next action in one sentence + one CTA.  
- [ ] No folders, tasks, comments, or team UI appear anywhere.  
- [ ] Public page works as a thumb-scroll on a phone-width layout.

---

# Next Phase (when approved)

Visual UI design (typography, spacing, components) → then architecture → then implementation.

Do not start visual mockups or code until this UX document is approved.

# ProjectHub — Product Requirements Document (PRD)

**Status:** Frozen for Version 1  
**Audience:** Founders, product, design, engineering  
**Scope:** Product only — no architecture or implementation

This document is the single source of truth for ProjectHub V1.

---

## 1. Product Overview

ProjectHub is a SaaS **Client Project Workspace** for freelancers, software agencies, and independent creators.

Every engagement lives as a **Project**. Each project has one dedicated workspace where the owner keeps delivery documents, important links, and client-facing progress posts — then shares a single public link so the client can access everything without chasing files.

ProjectHub is **not** a general file drive, a task manager, or a documentation wiki. It is the permanent home for client project delivery information.

---

## 2. Product Identity

| | |
|---|---|
| **Category** | Client Project Workspace |
| **Core Promise** | One Project. One Workspace. One Link. |
| **Primary Value** | Never resend project files again. |

---

## 3. Problem Statement

Project files and context are scattered across WhatsApp, email, Google Drive, Slack, Telegram, desktop folders, and Downloads.

After weeks or months:

- Finding the right document is slow and unreliable.
- Clients repeatedly ask developers to resend the same files.
- There is no single place that answers “what is this project, where is everything, and what changed?”

Folder-based tools do not solve this: they organize files, not **projects**, and they rarely give clients a clean, always-current view.

---

## 4. Why Now?

Freelancers and agencies are delivering more digital work than ever before.

A single project may involve PDFs, UI designs, GitHub repositories, staging URLs, API documentation, deployment links, invoices, and meeting notes.

Although cloud storage tools exist, they organize files—not project delivery.

Clients don't want folders.

They want one place that answers everything about the project.

ProjectHub exists to become that single destination.

---

## 5. Vision Statement

**Long term:** ProjectHub becomes the default client-facing workspace for how freelancers and agencies deliver work — one project, one home, one share link.

**Version 1:** Intentionally small. Nail the core loop: create a project, fill the workspace, share with the client, and let the client self-serve. Polish over breadth.

---

## 6. Target Users

**Primary (owners):**

- Freelancers  
- Software agencies  
- Web, mobile, and AI developers  
- Designers  
- Consultants  

**Secondary (recipients):**

- Clients who receive a share link  

Clients do **not** create accounts in V1. They only view and download.

---

## 7. User Journey

1. **Sign up / sign in** — Owner creates an account and reaches the dashboard.  
2. **Create project** — Owner names the project, adds a short overview, status starts as Active.  
3. **Upload files** — Owner adds the documents the client will need.  
4. **Add resources** — Owner saves permanent links (GitHub, Figma, production URL, docs, etc.).  
5. **Add progress** — Owner posts client-facing progress notes on the project timeline.  
6. **Share link** — Owner enables sharing and copies the public link to the client.  
7. **Client opens link** — Client sees the full workspace read-only: Overview, Files, Resources, and Progress; downloads as needed. No login.

Later, the owner can post more progress, change status (Completed / Archived), disable sharing, or regenerate the link (previous link stops working immediately).

---

## 8. Core Features

### Authentication

Owners sign up and sign in to access their projects. Sessions are private. Clients never authenticate in V1.

### Dashboard

The owner’s home list of projects, focused on **Active** and **Completed**. **Archived** projects are hidden from the main view but still reachable by the owner. Clear path to create a new project and open an existing workspace.

### Projects

A project is the atomic unit of ProjectHub.

- Has a name, overview, and status: **Active** (in progress), **Completed** (delivered, still accessible), **Archived** (off the main dashboard).  
- Belongs to the owner’s workspace.  
- Opening a project enters its dedicated workspace.

### Project Workspace

The heart of the product. One screen (or tightly connected view) that answers the four product questions at a glance: what this is, where files are, where links are, and what changed recently. Fast, minimal, and client-delivery oriented — not a file browser or a task board.

Workspace sections the client and owner both understand:

**Overview · Files · Resources · Progress**

### Files

Owners upload project documents into the workspace. Clients with a valid share link can view the list and download files. Owners can remove files they no longer want shared. The experience should feel like curated delivery assets, not an infinite personal drive.

### Resources

Permanent reference links for the project.

Each resource has:

- Title  
- URL  
- Type (e.g. GitHub, Figma, Production, Staging, API Docs, Other)  
- Optional description  

Resources help clients and owners jump to living tools and environments without digging through chat history.

### Progress

Client-facing progress posts that form the project timeline (newest first). This is what clients check when they want to know “what’s the latest?”

Each progress entry has:

- Title  
- Description  
- Created date  

Examples: “Authentication module completed.” “Deployment completed.” Progress replaces the need for constant “here’s the latest” messages.

### Public Share Page

One share link per project.

- **Enable** sharing → link works.  
- **Disable** sharing → link stops working.  
- **Regenerate** token → old link becomes invalid immediately.  

The public page shows the **entire** workspace in read-only mode: Overview, Files, Resources, Progress. Clients can view and download only. No edit, upload, or delete. Optimized for mobile, since clients often open links on phones.

---

## 9. Product Principles

A Project Workspace must always make these four answers obvious:

1. **What is this project?**  
2. **Where are all important files?**  
3. **Where are all important links?**  
4. **What changed recently?**  

Every future feature must strengthen at least one of these. If it does not, it does not belong in ProjectHub’s core product — especially not in Version 1.

---

## 10. Design Principles

ProjectHub should feel:

- Simple before powerful  
- Fast before feature-rich  
- Clean before colorful  
- Professional before trendy  
- Mobile-friendly by default  

Every screen should reduce friction.

Every interaction should require the fewest possible clicks.

---

## 11. Non-Goals

ProjectHub is not intended to replace:

- Google Drive  
- Dropbox  
- Notion  
- ClickUp  
- Jira  
- Trello  

The objective is not to manage work.

The objective is to **deliver** work.

**We don't manage work. We deliver work.**

---

## 12. Out of Scope (Version 1)

Version 1 will **not** include:

- AI  
- Chat  
- Team collaboration  
- Billing  
- Notifications  
- Analytics  
- Version history  
- Comments  
- Roles & permissions  
- Client accounts  

These may be considered only after V1 proves the core workspace and share loop.

---

## 13. Success Metrics

Version 1 succeeds when the happy path is effortless:

| Metric | Target |
|--------|--------|
| Time for an owner to create a project and open its workspace | Under 2 minutes |
| Time for an owner to enable sharing and copy the link | One clear action |
| Time for a client to find a needed file or resource on the public page | Under 30 seconds |
| Client follow-up | Client can self-serve without asking the owner to resend files |
| Share control | Owner can disable or regenerate the link and trust the old URL is dead |

Qualitative bar: the product feels small, polished, intuitive, and fast.

---

## 14. Product Philosophy

ProjectHub is not another file storage platform.

It is a dedicated **client project workspace** where every project has one permanent home — documents, links, and progress in one place, and one link for the client.

**One Project. One Workspace. One Link.**

Build the simplest version that makes that true. Then make it excellent.

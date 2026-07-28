# ProjectHub — Design System (Version 1)

**Status:** Draft for review (UI source of truth once approved)  
**Audience:** Design, engineering  
**Scope:** Visual language and component rules — no code, no mockups as final art  
**Depends on:** `docs/PRD.md` (frozen), `docs/UX.md` (approved)

**Inspiration (not imitation):** Linear’s density and calm, Vercel’s restraint, GitHub’s hierarchy, Notion’s quiet surfaces.  
**Original language name:** **Harbor** — cool, deep, steady. Premium without spectacle.

---

## 1. Design Intent

Harbor should feel:

| Feel | Means |
|------|--------|
| Premium | Precise spacing, restrained accent, no visual noise |
| Calm | Low contrast chrome, soft separators, no alarm colors in default UI |
| Professional | Neutral palette, clear type, predictable components |
| Fast | Instant feedback, minimal motion, obvious primary actions |

**Laws (from product)**

- Simple before powerful  
- Fast before feature-rich  
- Clean before colorful  
- Professional before trendy  
- Mobile-friendly by default  

**We don't manage work. We deliver work.** The UI should feel like a delivery desk, not a productivity carnival.

---

## 2. Color System

Dark mode is the default product surface. Light mode may follow later; V1 ships dark-first.

### 2.1 Neutrals (Canvas & Ink)

Name tokens semantically. Do not invent one-off hex in components.

| Token | Role | Dark value (reference) |
|-------|------|-------------------------|
| `canvas` | App background | `#0B0D10` |
| `canvas-elevated` | Panels, dropdowns | `#12151A` |
| `surface` | Cards, inputs, list rows | `#161A21` |
| `surface-hover` | Hover wash | `#1C222B` |
| `border` | Default hairline | `#2A313C` |
| `border-subtle` | Quiet dividers | `#1F252E` |
| `border-strong` | Focus rings adjacent / emphasis | `#3D4654` |
| `ink` | Primary text | `#ECEFF3` |
| `ink-secondary` | Secondary text | `#9AA3B2` |
| `ink-tertiary` | Placeholder, meta | `#6B7380` |
| `ink-inverse` | Text on accent | `#061016` |

### 2.2 Accent (Harbor Teal)

One accent family only. No second brand color in V1.

| Token | Role | Value (reference) |
|-------|------|-------------------|
| `accent` | Primary actions, key focus | `#3DB8A8` |
| `accent-hover` | Primary hover | `#4EC9B9` |
| `accent-muted` | Soft badges, selected wash | `#3DB8A814` |
| `accent-border` | Selected ring / chip | `#3DB8A855` |

### 2.3 Semantic

| Token | Role | Value (reference) |
|-------|------|-------------------|
| `danger` | Destructive | `#E57272` |
| `danger-muted` | Destructive wash | `#E572721A` |
| `warning` | Caution (regenerate share) | `#D6A85C` |
| `success` | Saved / copied | `#5BB98C` |
| `focus` | Focus ring | `#3DB8A8` @ 2px |

### 2.4 Color Rules

- Never use accent for large background fills.  
- Status pills use neutral + label; Active may use `accent-muted`, Completed neutral, Archived tertiary.  
- Public share page uses the same tokens (familiar, trustworthy).  
- No gradients on surfaces. No glow. No rainbow badges.

---

## 3. Typography Scale

### 3.1 Families

| Role | Family | Notes |
|------|--------|--------|
| UI Sans | **Satoshi** (or equivalent geometric neo-grotesk) | Primary UI; fallback: `ui-sans-serif, system-ui, sans-serif` |
| Mono | **IBM Plex Mono** | URLs, tokens, file sizes optional; fallback: `ui-monospace, monospace` |

Do not use Inter, Roboto, Arial as the intended brand face. System fallbacks are fine for loading.

### 3.2 Scale

| Token | Size / Line | Weight | Use |
|-------|-------------|--------|-----|
| `display` | 32px / 40px | 600 | Landing hero product name only |
| `title-1` | 24px / 32px | 600 | Page titles (Dashboard, Settings) |
| `title-2` | 20px / 28px | 600 | Project name in workspace header |
| `title-3` | 16px / 24px | 600 | Section titles, dialog titles |
| `body` | 14px / 20px | 400 | Default body, form values |
| `body-strong` | 14px / 20px | 500–600 | List primary labels, button labels |
| `caption` | 12px / 16px | 400 | Meta: dates, file sizes, helper |
| `micro` | 11px / 14px | 500 | Eyebrows, overline labels (rare) |

### 3.3 Type Rules

- Default UI size is **14px**. Do not inflate body to 16px everywhere.  
- Tracking: slight negative (−0.01em) on `title-1` / `title-2`; default elsewhere.  
- One weight ladder: 400 / 500 / 600 only. No 900.  
- Links in content use accent underline on hover only; nav links use ink, not underline.  
- Public page Overview body may use `body` at comfortable length; avoid long essay styling.

---

## 4. Spacing System

Base unit: **4px**.

| Token | Value |
|-------|-------|
| `space-0` | 0 |
| `space-1` | 4px |
| `space-2` | 8px |
| `space-3` | 12px |
| `space-4` | 16px |
| `space-5` | 20px |
| `space-6` | 24px |
| `space-8` | 32px |
| `space-10` | 40px |
| `space-12` | 48px |
| `space-16` | 64px |

### Layout rhythm

| Context | Padding |
|---------|---------|
| Page horizontal (desktop) | `space-8` (32px) |
| Page horizontal (mobile) | `space-4` (16px) |
| Card / panel padding | `space-4`–`space-6` |
| Stack between sections | `space-8` |
| Stack between related items | `space-2`–`space-3` |
| Form field gap | `space-4` |
| Compact list row height | 40–44px |
| Comfortable list row height | 48–52px |

**Rule:** Prefer consistent vertical rhythm over one-off margins. If unsure, use `space-4`.

---

## 5. Border Radius

| Token | Value | Use |
|-------|-------|-----|
| `radius-none` | 0 | Tables (optional), hairlines |
| `radius-sm` | 6px | Inputs, buttons (sm), chips |
| `radius-md` | 8px | Buttons (default), menu items |
| `radius-lg` | 12px | Cards, dialogs, dropdowns |
| `radius-xl` | 16px | Landing hero panels only (rare) |
| `radius-full` | 9999px | Avatars only — **not** buttons or filters |

**Rule:** Avoid pill-shaped primary buttons. Harbor uses soft rectangles, not capsules.

---

## 6. Shadows & Elevation

Harbor is mostly border-driven, not shadow-driven.

| Token | Use | Spec (reference) |
|-------|-----|------------------|
| `shadow-none` | Default surfaces | — |
| `shadow-sm` | Dropdowns, popovers | `0 4px 16px rgba(0,0,0,0.35)` |
| `shadow-md` | Dialogs / modals | `0 12px 40px rgba(0,0,0,0.45)` |

**Rules**

- Cards on canvas: **border only**, no shadow.  
- No multi-layer colored glows.  
- Focus is a **ring**, not a shadow.

---

## 7. Icon Style

| Attribute | Spec |
|-----------|------|
| Family | Outline / stroke icons (Lucide-compatible metaphor set) |
| Stroke | 1.5–1.75px |
| Size | 16px default; 14px in dense tables; 20px for empty-state illustration icons |
| Cap / join | Round |
| Color | Inherit `ink-secondary`; `ink` on hover; `accent` only for selected/active |
| Grid | Optical square; align to text cap-height in buttons |

**Rules**

- No filled duotone icons in V1.  
- No emoji as UI icons.  
- Pair icon + label for primary nav and empty CTAs; icon-only only when space-constrained with aria-label (e.g. download, delete).

---

## 8. Motion

| Token | Duration | Easing |
|-------|----------|--------|
| `motion-fast` | 120ms | ease-out |
| `motion-base` | 180ms | ease-out |
| `motion-slow` | 240ms | ease-in-out |

Use for: hover fades, dialog enter/exit, toast in/out.  
**Do not:** page parallax, large spring bounce, skeleton shimmer as decoration.

Respect `prefers-reduced-motion`: disable non-essential transitions.

---

## 9. Component Inventory (V1)

Build only what UX needs.

### Foundations
- Color tokens, type tokens, space tokens  
- Icon wrapper  
- Focus ring utility  

### Actions
- Button (primary, secondary, ghost, danger, icon)  
- Link (inline, quiet)  
- Menu / dropdown  
- Tabs (workspace sections)  
- Segmented control (dashboard status filter)  

### Forms
- Text input  
- Textarea  
- Select  
- Label + hint + error  
- Checkbox (rare)  
- Password field with show/hide  

### Feedback
- Toast  
- Inline alert  
- Empty state  
- Skeleton (list load only)  
- Spinner / button loading  

### Overlays
- Dialog / modal  
- Confirm dialog  
- Dropdown panel  
- Create Project modal  

### Data display
- Table / list row  
- Status pill  
- Resource type chip  
- File row  
- Progress timeline item  
- Meta text (date, size)  

### Navigation & shell
- App top bar  
- Account menu  
- Project workspace header  
- Share control cluster  
- Public page header (minimal)  
- Breadcrumb-style back control  

### Content
- Page header  
- Section header  
- Divider  
- Card (use sparingly — see below)

---

## 10. Button Hierarchy

| Variant | When | Style cues |
|---------|------|------------|
| **Primary** | One main action per view (Create, Save, Enable sharing, Sign in) | `accent` fill, `ink-inverse` text |
| **Secondary** | Alternative equal-weight (Cancel next to Create is ghost/secondary) | `surface` + `border`, `ink` text |
| **Ghost** | Tertiary, toolbar, Cancel | Transparent, hover `surface-hover` |
| **Danger** | Delete, destructive confirm | `danger` text or fill on confirm step |
| **Icon** | Download, more, close | Ghost + 16px icon; min hit 32×32 |

### Size

| Size | Height | Pad X | Type |
|------|--------|-------|------|
| `sm` | 32px | 12px | `caption` / `body` 13–14 |
| `md` | 36px | 14px | `body-strong` |
| `lg` | 40px | 16px | `body-strong` — landing / auth only |

### Rules

- One primary button per visible region.  
- Destructive actions never primary-colored teal.  
- Loading: keep button width, show spinner, disable double-submit.  
- Do not use pill (`radius-full`) buttons.

---

## 11. Form Components

### Anatomy
`Label` → `Control` → `Hint` (optional) → `Error` (replaces hint)

### Text input / Textarea
- Height input: 36px (`md`)  
- Radius: `radius-sm`  
- Background: `surface`  
- Border: `border`; focus: `accent` ring 2px + border-strong  
- Placeholder: `ink-tertiary`  

### Select
- Same metrics as input  
- Chevron 16px, `ink-secondary`  

### Validation
- Error text: `caption` + `danger`  
- Do not rely on color alone — text required  

### Auth forms
- Max width ~360–400px, centered  
- Vertical stack `space-4`  

---

## 12. Card Components

**Default philosophy:** Prefer flat canvas + dividers over card grids (matches UX / PRD).

| Use cards | Avoid cards |
|-----------|-------------|
| Dialogs, dropdown panels, marketing “how it works” steps if needed | Dashboard project list, file list, timeline |
| Settings grouped sections (optional subtle surface) | Wrapping every workspace section |

**Card spec (when used)**
- Background: `canvas-elevated` or `surface`  
- Border: `border-subtle`  
- Radius: `radius-lg`  
- Padding: `space-4`–`space-6`  
- Shadow: none on page; `shadow-sm` only if floating  

---

## 13. Empty States

### Anatomy
1. Optional 20px outline icon (`ink-tertiary`)  
2. Title (`title-3`)  
3. One sentence (`body` / `ink-secondary`)  
4. One primary CTA  

### Copy tone
Short, confident, instructional. No jokes. No multi-step tours.

### Placement
Centered in the content region below section header; not a full-page marketing block inside the app.

---

## 14. Toasts

| Kind | Use |
|------|-----|
| Success | Copied link, saved, uploaded |
| Error | Upload failed, save failed |
| Warning | Rare; prefer dialog for regenerate |

### Spec
- Position: bottom-center (owner app) or bottom-center on public  
- Max width: 360px  
- Duration: 3s success; 5s error (or sticky with dismiss)  
- Stack max: 2  
- Motion: `motion-base`  

Do not toast for every navigation. Prefer inline errors on forms.

---

## 15. Dialogs

### Types
1. **Form dialog** — Create Project, Add Resource, Add Progress  
2. **Confirm dialog** — Delete file, Disable share, Regenerate link  

### Spec
- Width: 400–480px (form), 400px (confirm)  
- Radius: `radius-lg`  
- Overlay: `canvas` at ~60% opacity  
- Shadow: `shadow-md`  
- Title: `title-3`  
- Body: `body` + `ink-secondary`  
- Footer: right-aligned actions; destructive confirm uses Danger button  

### Rules
- Esc and overlay click dismiss non-destructive dialogs.  
- Destructive confirms: require explicit button; no overlay-click dismiss.  
- Focus trap + return focus to trigger.

---

## 16. Tables & Lists

Harbor prefers **list rows** over heavy data-grid chrome.

### Project list / Files list
- Header optional (desktop); columns align  
- Row hover: `surface-hover`  
- Separator: `border-subtle` hairline  
- Primary text: `body-strong`  
- Meta: `caption` + `ink-tertiary`  
- Actions: appear on hover (desktop); always visible icon buttons on touch  

### Progress timeline
- Not a table — stacked entries with date `caption`, title `body-strong`, body `body`  
- Newest first  
- Quiet top border between items  

### Resources
- Type chip + title + truncated URL (mono optional for URL)  

---

## 17. Navigation

### App top bar
- Height: 48–56px  
- Left: wordmark “ProjectHub” (not a loud logo lockup)  
- Right: account menu  
- Border bottom: `border-subtle`  
- Background: `canvas`  

### Dashboard filters
- Segmented control: Active | Completed | Archived  
- Active segment: `accent-muted` + `accent` text  

### Workspace section tabs
- Text tabs: Overview | Files | Resources | Progress  
- Active: `ink` + accent underline 2px  
- Inactive: `ink-secondary`  
- Mobile: horizontal scroll tabs, no wrap into hamburger for four items  

### Back control
- “← Projects” ghost control; not a nested breadcrumb trail  

### Public page
- No app top bar  
- Project name as `title-2`  
- No account menu  

### Share cluster
- Treat as header actions; Copy uses secondary/ghost; Enable uses primary when off  

---

## 18. Status & Chips

### Project status pill
| Status | Treatment |
|--------|-----------|
| Active | `accent-muted` bg, accent text |
| Completed | `surface-hover` bg, `ink-secondary` text |
| Archived | transparent, `ink-tertiary` text, subtle border |

### Resource type chip
- Compact `caption`, `surface-hover`, `radius-sm`  
- Label only (GitHub, Figma, Prod…) — no colored brand logos required in V1  

---

## 19. Mobile Rules

| Breakpoint | Width |
|------------|-------|
| Mobile | &lt; 640px |
| Tablet | 640–1024px |
| Desktop | &gt; 1024px |

### Owner app
- Desktop-first layouts; usable on tablet  
- Dashboard: full-width list; Create button sticky or top-right  
- Workspace: tabs scroll horizontally  
- Dialogs: full-width sheet on mobile (`radius-lg` top only optional) — V1 may use full-screen takeovers for Create/Edit  

### Public share page (priority)
- Phone-first  
- Single column  
- Order: Overview → Progress → Resources → Files  
- Hit targets ≥ 44px for Open / Download  
- No hover-only actions  

### General
- Page padding `space-4` on mobile  
- Avoid hover-dependent critical actions  
- Sticky share controls are owner-only; clients don’t need them  

---

## 20. Accessibility Rules

- Contrast: text/`ink` on `canvas` and `surface` must meet WCAG AA.  
- Focus visible on all interactive elements (`focus` ring, never remove outline without replacement).  
- Icon-only buttons: `aria-label`.  
- Dialogs: role="dialog", labelled by title, focus trap.  
- Toasts: `aria-live="polite"` (assertive for errors).  
- Status not by color alone — include text label.  
- Forms: labels associated with inputs; errors linked via `aria-describedby`.  
- Hit target minimum 32px desktop, 44px preferred on public mobile.  
- Respect `prefers-reduced-motion`.  
- Keyboard: full path for create project, upload trigger, share copy, tab navigation.  
- Public page: semantic headings (one `h1` = project name).  

---

## 21. Content & Microcopy Style

- Sentence case for buttons: “Create project”, “Enable sharing”, “Copy link”  
- No exclamation marks in product UI  
- Errors: calm and specific (“Upload failed. Try again.”)  
- Share regenerate confirm: clear consequence (“The current link will stop working immediately.”)  

---

## 22. Do / Don’t

| Do | Don’t |
|----|-------|
| One accent, lots of neutral | Purple gradients, glow, glassmorphism |
| Border + surface elevation | Drop shadows on every card |
| Dense, readable lists | Oversized marketing cards in the app |
| Soft rectangle controls | Pill CTAs everywhere |
| Empty state → one CTA | Empty state carousels |
| Public page as status document | Public page as mini dashboard |

---

## 23. Handoff Checklist (before UI implementation)

- [ ] Tokens named and documented (color, type, space, radius, shadow, motion)  
- [ ] Component inventory matches `docs/UX.md` screens  
- [ ] Button hierarchy agreed  
- [ ] Public page mobile rules agreed  
- [ ] Accessibility rules accepted  

**Next phase (when this document is approved):** UI implementation with shadcn/ui mapped to Harbor tokens — still architecture/plan before large coding milestones per project rules.

---

## 24. Philosophy

Harbor is quiet on purpose.

The project content is the hero — names, files, links, and progress — not the chrome.

If a visual choice competes with the four questions (what / files / links / latest), remove it.

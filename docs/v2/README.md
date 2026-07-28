# ProjectHub V2 documents

**Documentation status: ALIGNED (review decisions applied)**  
**Implementation:** Milestone-gated per [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) (greenfield pivot; stop after each milestone for review)

V2 is a **product pivot** (Versioned Client Delivery Platform), not an incremental extension of V1.

| Document | Path |
|----------|------|
| PRD | [PRD.md](./PRD.md) |
| UX | [UX.md](./UX.md) |
| Data Model | [DATA_MODEL.md](./DATA_MODEL.md) |
| API Contract | [API_CONTRACT.md](./API_CONTRACT.md) |
| Implementation Plan | [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) |

V1 docs under `docs/*.md` remain historical / frozen for the completed V1 workspace product.

**Rules**
- Treat V2 docs as the only product source of truth.
- Client Portal delivery content uses **immutable published versions only** — never Draft.
- Portal **name** comes from the Version snapshot; portal **status** comes from the live project.
- Progress timeline (V1) is replaced by **Release Notes** on Versions.
- Soft-delete is the only project state that removes portal access among lifecycle outcomes; Completed and Archived remain shareable.
- No V1 content backfill (greenfield). Do not continue past a milestone without approval.

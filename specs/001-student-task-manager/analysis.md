# Specification Analysis Report (`/speckit.analyze`)

**Date**: 2026-10-13 · **Artifacts**: spec.md, plan.md, tasks.md, data-model.md,
contracts/openapi.yaml · **Constitution**: v1.0.0

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|---|---|---|---|---|---|
| A1 | Coverage gap | Medium | spec NFR-02 / tasks | Page-load time (NFR-02) had no task; T039 only timed API calls. | T038 now also records page-load time. |
| A2 | Inconsistency | Medium | spec US7 §4 vs FR-30 | Story says admins cannot *demote* the main admin or themselves; FR-30 only covered deactivation and never said admins can change roles. | FR-30 amended: admins can change roles; main admin and self are protected for both actions. Contract already had `role` on PATCH /admin/users/{id}. |
| A3 | Underspecified (accepted) | Low | FR-07 | "after confirming" can only be enforced in the UI; the API deletes on request. | Accepted: confirmation is a UI duty (task T022); noted here. |
| A4 | Ambiguity check | — | Priority section | Every time-to-deadline now maps to exactly one band; rounding and level order stated. | None needed (closed in Clarifications). |
| A5 | Constitution | — | plan.md | All six principles pass; no complexity exceptions. | None. |
| A6 | Terminology | Low | spec / contract | Spec says "shown score"; contract field is `priority.score` with `exact` beside it. | Contract description states `score` = shown score. |

## Coverage summary

| Requirement group | Tasks | Covered |
|---|---|---|
| FR-01–03 Account | T015–T017 | ✔ |
| FR-04–10 Tasks + validation | T018, T020–T022 | ✔ |
| FR-11–14 Priority | T013–T014 | ✔ |
| FR-15–18 Organisation | T023–T025 | ✔ |
| FR-19–20 Dashboard | T026–T028 | ✔ |
| FR-21 Isolation | T019, T020 | ✔ |
| FR-22–25 Profile | T005, T029–T031 | ✔ |
| FR-26–32 Admin | T005, T032–T034 | ✔ |
| FR-33–35 Interface | T011, T021, T038 | ✔ |
| NFR-01–16 | T007, T008, T011, T038, T039, T042 | ✔ (NFR-14 is a team action) |

**Metrics**: 35 functional + 16 non-functional requirements; 42 tasks; 0 requirements
without a task after fixes; 0 critical issues. Ready for `/speckit.implement`.

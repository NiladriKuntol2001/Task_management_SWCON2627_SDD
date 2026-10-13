---
description: "Task list for StudyFlow SDD v1"
---

# Tasks: StudyFlow — Smart Student Task Manager (SDD v1)

**Input**: `plan.md`, `spec.md`, `data-model.md`, `contracts/openapi.yaml`, `research.md`

**Tests**: Required by the constitution (principle III). Test tasks come before the
code they test inside each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency)
- **[Story]**: US1–US8 from spec.md

## Phase 1: Setup

- [x] T001 Create structure from plan.md (`backend/app`, `backend/tests`, `frontend`, `seed`, `e2e`, `docs/sdd`)
- [x] T002 [P] `backend/requirements.txt` (starlette, uvicorn, pydantic, PyJWT) and `.gitignore`
- [x] T003 [P] `run.py` with `--seed`, `--reset`, `--host`, `--port`

## Phase 2: Foundational (blocks all stories)

- [x] T004 `backend/app/config.py` — settings from env (DB path, secret, token lifetime)
- [x] T005 `backend/app/db.py` — schema (data-model.md), foreign keys, main-admin bootstrap [FR-25, FR-26]
- [x] T006 [P] `backend/app/errors.py` — ApiError, JSON error shape (contract)
- [x] T007 [P] `backend/app/security.py` — scrypt hashing, JWT issue/verify, revocation, `require_user`, `require_admin` [NFR-03, NFR-04]
- [x] T008 [P] `backend/app/validation.py` — request models with field messages [FR-10, NFR-06, NFR-07]
- [x] T009 `backend/app/main.py` — app factory, routing, static frontend, error handlers
- [x] T010 `backend/tests/support.py` — live test server on a free port + JSON client
- [x] T011 [P] `frontend/css/app.css` — light/dark tokens, layout shell, breakpoints 960/820/600 [FR-33, FR-34, NFR-15, NFR-16]
- [x] T012 [P] `frontend/js/api.js`, `ui.js`, `format.js`, `app.js` — fetch wrapper, toasts, modal, router, shell

**Checkpoint**: server starts, `/api/health` answers, empty shell renders in both themes.

## Phase 3: US3 — Priority engine (P1) 🎯 core rule first

- [x] T013 [US3] `backend/tests/test_priority.py` — bands incl. clarified edges, rounding, levels, tie order [FR-11..14]
- [x] T014 [US3] `backend/app/priority.py` — locked formula, `score()`, `sort_key()` [FR-11..14]

## Phase 4: US1 — Account (P1)

- [x] T015 [US1] `backend/tests/test_auth.py` — register, duplicate email, login, wrong password, logout revokes, persistence [FR-01..03, NFR-10]
- [x] T016 [US1] `backend/app/users_repo.py` + `routes/auth.py` [FR-01..03]
- [x] T017 [US1] `frontend/js/views/login.js` — sign-in / create-account screen

## Phase 5: US2 — Manage tasks (P1)

- [x] T018 [US2] `backend/tests/test_tasks.py` — CRUD, validation messages, complete/reopen, preview [FR-04..10, FR-35]
- [x] T019 [US2] `backend/tests/test_isolation.py` — other users' tasks are 404 for read/edit/complete/delete [FR-21, NFR-05]
- [x] T020 [US2] `backend/app/tasks_repo.py` + `routes/tasks.py` [FR-04..10, FR-21, FR-35]
- [x] T021 [US2] `frontend/js/views/task-form.js` — add/edit form with live preview [FR-04..06, FR-10, FR-35]
- [x] T022 [US2] `frontend/js/views/task-detail.js` — details + breakdown, complete, delete with confirm [FR-07..09]

## Phase 6: US4 — Organise (P2)

- [x] T023 [US4] Tests for filters, sort, upcoming, overdue in `test_tasks.py` [FR-15..18]
- [x] T024 [US4] Filters/sort/views in `routes/tasks.py` + `tasks_repo.py` [FR-15..18]
- [x] T025 [US4] `frontend/js/views/tasks.js` — list with status/subject chips, search, sort; Upcoming/Overdue/Completed presets [FR-15..18, FR-34]

## Phase 7: US5 — Dashboard (P2)

- [x] T026 [US5] `backend/tests/test_dashboard.py` — counts, mix, recommendation, empty state [FR-19, FR-20]
- [x] T027 [US5] `backend/app/recommendation.py` + `routes/dashboard.py` [FR-19, FR-20]
- [x] T028 [US5] `frontend/js/views/dashboard.js` — matches approved design

## Phase 8: US6 — Profile (P3)

- [x] T029 [US6] `backend/tests/test_profile.py` — view, email rules, password rules, old password stops working [FR-22..25]
- [x] T030 [US6] `routes/profile.py` [FR-22..25]
- [x] T031 [US6] `frontend/js/views/profile.js` — live rule checklist

## Phase 9: US7 — Admin (P3)

- [x] T032 [US7] `backend/tests/test_admin.py` — 403 for students, main admin bootstrap and protection, deactivate blocks login and live sessions, overview numbers, user search, create user, all-tasks filters [FR-26..32]
- [x] T033 [US7] `routes/admin.py` [FR-26..32]
- [x] T034 [US7] `frontend/js/views/admin.js` — overview, users, all tasks

## Phase 10: Sample data and oracle

- [x] T035 [P] `seed/generate_seed.py` (independent formula) → `seed/seed-data.json`
- [x] T036 `backend/app/seed.py` — load with deadlines relative to now
- [x] T037 `backend/tests/test_seed_oracle.py` — every open seed task's API score/level equals the oracle [SC-001]

## Phase 11: Polish and verification

- [x] T038 [US8] `e2e/e2e.mjs` — Playwright run-through (register, add task, complete, theme switch, admin) + screenshots at 390/768/1280 px + page-load timing [FR-33, FR-34, SC-005, NFR-02]
- [x] T039 Performance check: time each API call on the sample data [NFR-01, SC-006]
- [x] T040 `docs/sdd/traceability.md` — FR/NFR → code → test → result
- [x] T041 `README.md` — run, test, accounts, SDD artifact map
- [ ] T042 Team review of AI-generated code recorded in `docs/sdd/review-log.md` [NFR-14] — **team action**

## Dependencies

Setup → Foundational → US3 (priority) → US1 → US2 → US4/US5 (parallel) → US6/US7
(parallel) → sample data → polish. Frontend views follow their backend story.

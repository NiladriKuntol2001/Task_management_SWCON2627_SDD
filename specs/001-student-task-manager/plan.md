# Implementation Plan: StudyFlow — Smart Student Task Manager (SDD v1)

**Branch**: `001-student-task-manager` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-student-task-manager/spec.md`

## Summary

A web app where students manage tasks and get a priority score (locked 50/30/20
formula) and a daily recommendation, with a profile page and an admin panel. Python
ASGI backend with SQLite, JSON API, and a no-build JavaScript frontend that follows
the approved light/dark responsive design. Decisions and alternatives: [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.11+ (backend), JavaScript ES2020 modules (frontend)

**Primary Dependencies**: Starlette, Uvicorn, PyJWT (see `backend/requirements.txt`).
*Amended during implementation:* Pydantic was dropped — hand-written validators give
the exact field messages FR-10/NFR-07 ask for with less code.

**Storage**: SQLite file (`data/studyflow.db`), standard-library `sqlite3`

**Testing**: `unittest` (unit + API against a live server), Playwright script (E2E, screenshots)

**Target Platform**: Any OS with Python 3.11+; modern browsers

**Project Type**: Web application (backend API + static frontend served by the backend)

**Performance Goals**: API and page loads < 2 s (NFR-01/02); expected < 100 ms locally

**Constraints**: No decorative animation; WCAG AA contrast; works at 390 px width

**Scale/Scope**: Tens of users, hundreds of tasks; 11 screens

## Constitution Check

*GATE: checked before research and again after design.*

| Principle | How the plan meets it | Status |
|---|---|---|
| I. Spec is source of truth | Tasks reference FR IDs; traceability matrix in `docs/sdd/traceability.md` | Pass |
| II. Priority locked, one module | `priority.py` only; preview endpoint for the UI (R6) | Pass |
| III. Every requirement tested | Test files per module; matrix maps FR → test | Pass |
| IV. Own data only | Every task query takes `owner_id`; foreign IDs return 404 | Pass |
| V. Secure by default | scrypt hashes (R3), server-side validation (`validation.py`), token revocation (R4) | Pass |
| VI. Simple, modular, few deps | 3 runtime packages; modules per NFR-13 | Pass |

Re-check after Phase 1 design: **Pass** (no violations; Complexity Tracking empty).

## Project Structure

### Documentation (this feature)

```text
specs/001-student-task-manager/
├── spec.md              # /speckit.specify + /speckit.clarify
├── checklists/requirements.md   # /speckit.checklist
├── research.md          # Phase 0
├── plan.md              # this file
├── data-model.md        # Phase 1
├── contracts/openapi.yaml       # Phase 1
├── quickstart.md        # Phase 1
├── tasks.md             # /speckit.tasks
└── analysis.md          # /speckit.analyze
```

### Source Code (repository root)

```text
run.py                      # start server (serves API + frontend); --seed, --reset
backend/
├── requirements.txt
├── app/
│   ├── main.py             # create_app(): routes, static files, error handling
│   ├── config.py           # settings from environment
│   ├── db.py               # connection, schema, main-admin bootstrap
│   ├── errors.py           # ApiError + JSON error responses
│   ├── security.py         # password hashing, JWT, revocation, current-user guards
│   ├── validation.py       # request validation + friendly field messages
│   ├── priority.py         # THE formula (FR-11..14) — nowhere else
│   ├── users_repo.py       # user SQL
│   ├── tasks_repo.py       # task SQL (always filtered by owner)
│   ├── recommendation.py   # FR-20
│   ├── seed.py             # load seed/seed-data.json
│   └── routes/
│       ├── auth.py         # FR-01..03
│       ├── tasks.py        # FR-04..18, FR-35 preview
│       ├── dashboard.py    # FR-19, FR-20
│       ├── profile.py      # FR-22..25
│       └── admin.py        # FR-26..32
└── tests/                  # unittest suites, one per module
frontend/
├── index.html
├── css/app.css             # design tokens (light/dark), layout, responsive rules
└── js/
    ├── app.js              # boot, router, layout shell
    ├── api.js              # fetch wrapper, token storage, errors
    ├── ui.js               # shared components (badges, toasts, modal, icons)
    ├── format.js           # dates and labels
    └── views/              # login, dashboard, tasks, task-form, task-detail,
                            # profile, admin-overview, admin-users, admin-tasks
seed/
├── generate_seed.py        # independent oracle for expected scores
└── seed-data.json
e2e/e2e.mjs                 # Playwright run-through + screenshots
docs/sdd/                   # process log, traceability, review log
```

**Structure Decision**: Web application with the frontend served as static files by
the backend, so one command runs everything and there is no CORS configuration.

## Key Design Decisions

- **Priority computed on read**: scores depend on the current time, so they are
  calculated whenever tasks are returned (FR-13) and never stored.
- **Information hiding**: `priority.py` exposes `score(deadline, difficulty, hours,
  now)` and `sort_key(...)`; weights and bands are private constants. Repositories hide
  SQL; routes never write SQL.
- **Errors**: every error is `{"error": {"message": str, "fields": {name: message}}}`
  with status 401, 403, 404, 409 or 422 (contract).
- **Security (STRIDE pass)**: Spoofing → scrypt + JWT; Tampering → server-side
  validation, owner filter on writes; Repudiation → `created_at` / `completed_at`;
  Information disclosure → 404 for foreign tasks, no password hashes in responses,
  identical login error for unknown email and wrong password; Denial of service →
  input length limits; Elevation of privilege → role checked on every admin request,
  main admin protected.
- **Frontend**: CSS custom properties for both themes (`[data-theme]`), media queries
  at 960/820/600 px per the design; no CSS transitions or animations.

## Complexity Tracking

No violations.

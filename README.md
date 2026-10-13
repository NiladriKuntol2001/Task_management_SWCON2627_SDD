# StudyFlow — Smart Student Task Manager (SDD v1)

A web app where students manage assignments, exams and projects. Each task gets a
priority score from the locked 50/30/20 formula (deadline, difficulty, estimated time),
and the dashboard answers **"What should I work on today?"**. Includes a student profile,
an admin panel, light and dark themes, and a layout that works from phone to desktop.

This repository is the **Spec-Driven Development (SDD)** track of the SWCON2627 course
project (Zahra, Niladri, Khadija). It was built with GitHub Spec-Kit's workflow; the
vibe-coded versions live in the separate repository `Task_management_SWCON2627`.

## Run it

Needs Python 3.11 or newer.

```bash
python -m pip install -r backend/requirements.txt
python run.py --seed          # first run: creates data/studyflow.db with sample data
```

Open http://127.0.0.1:8000. Later runs: `python run.py` (keeps data).
`python run.py --reset --seed` starts over with fresh sample data.

### Sample accounts

| Who | Email | Password |
|---|---|---|
| Main admin (ID 1) | admin123@gmail.com | admin@123 |
| Niladri (ID 2, 17 tasks) | niladri@student.test | Student@123 |
| Zahra, Khadija, Aino, Mikael (IDs 3–6) | zahra@ / khadija@ / aino@ / mikael@student.test | Student@123 |
| Sara (ID 7, deactivated) | sara@student.test | cannot sign in |

The sample deadlines are placed relative to the moment you load them, so the
dashboard looks the same on any day. **Change the admin password** (Profile) before
anyone else can reach the app.

## Test it

```bash
python -m unittest discover -s backend/tests -t . -v     # 85 unit + API tests
```

Browser run-through (66 checks + screenshots at 390 / 768 / 1280 px, both themes):

```bash
python run.py --reset --seed --port 8765                 # in one terminal
cd e2e && npm install && npx playwright install chromium && node e2e.mjs http://127.0.0.1:8765
```

## How SDD was applied — where to find each artifact

| Spec-Kit step | Artifact |
|---|---|
| `/speckit.constitution` | `.specify/memory/constitution.md` |
| `/speckit.specify` + `/speckit.clarify` | `specs/001-student-task-manager/spec.md` (see *Clarifications*) |
| `/speckit.checklist` | `specs/001-student-task-manager/checklists/requirements.md` |
| `/speckit.plan` | `plan.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`, `quickstart.md` |
| `/speckit.tasks` | `specs/001-student-task-manager/tasks.md` |
| `/speckit.analyze` | `specs/001-student-task-manager/analysis.md` |
| `/speckit.implement` | the code, built test-first; commit messages cite task and requirement IDs |
| Verification | `docs/sdd/traceability.md`, `docs/sdd/e2e-results.txt` |
| Process notes for the report | `docs/sdd/process-log.md` |
| Human review (NFR-14) | `docs/sdd/review-log.md` — **to be filled in by the team** |

Spec-Kit templates and scripts are in `.specify/` (from github/spec-kit, MIT licence).
To get the `/speckit.*` slash commands in your own AI agent, run
`specify init --here --integration claude` (or `--integration copilot`) in this folder.

## Stack

Python · Starlette + Uvicorn · SQLite · PyJWT · scrypt password hashing ·
plain HTML/CSS/JavaScript (no build step). Reasons and rejected alternatives:
`specs/001-student-task-manager/research.md`.

```
run.py            start the app
backend/app/      API: auth, tasks, priority (the only place the formula lives),
                  recommendation, profile, admin, seed loader
backend/tests/    unittest suites (one per module) + seed oracle
frontend/         index.html, css/app.css, js/ (router, api client, views)
seed/             generate_seed.py (independent oracle) → seed-data.json
e2e/              Playwright run-through
specs/, docs/     SDD artifacts
```

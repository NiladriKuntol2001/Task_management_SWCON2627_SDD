# Agent guidance — StudyFlow SDD v1

This repository is built with Spec-Driven Development (GitHub Spec-Kit).

- Rules: `.specify/memory/constitution.md` (read first; it overrides everything else).
- What to build: `specs/001-student-task-manager/spec.md`.
- How it is built: `specs/001-student-task-manager/plan.md`, `data-model.md`, `contracts/openapi.yaml`.
- Work items: `specs/001-student-task-manager/tasks.md`.

Rules that bite:

- Never change the priority formula or its tables; it lives only in `backend/app/priority.py`.
- Change `spec.md` before changing behaviour, in the same commit.
- Every task query is filtered by the current user (FR-21).
- Run tests: `python -m unittest discover -s backend/tests -t .` and `node e2e/e2e.mjs` (needs a running server).

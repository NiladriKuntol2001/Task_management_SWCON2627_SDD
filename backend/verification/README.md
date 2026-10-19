# Independent verification of the SDD build (Member 3)

This folder holds the verification suite written by Khadija Bassoum from the team specification and decisions D1–D4. It is the same suite that was run on the Vibe Coding build: same test cases, same IDs (TC-AUTH, TC-TASK, TC-PRI, TC-FLT, TC-SORT, TC-UPC, TC-OVD, TC-DASH, TC-REC, TC-SEC, TC-NFR) and the same hand-calculated expected values. Only the calls were adapted to this build's interface.

## Run

From the repository root:

```bash
pip install -r backend/requirements.txt pytest pytest-cov httpx
pytest backend/verification -v                                        # this suite
pytest backend/tests backend/verification --cov=backend/app            # with the developer tests
```

Each test gets its own temporary database, so the suite never touches `data/`.

## How the interface differs from the Vibe Coding build

| Vibe Coding build | SDD build | Effect on the test |
| --- | --- | --- |
| `/tasks`, `/dashboard`, `/auth/me` | `/api/tasks`, `/api/dashboard`, `/api/me` | path only |
| `access_token` in the login answer | `token` | key only |
| list returns `[...]` | list returns `{"tasks": [...], "subjects", "counts"}` | read `tasks` |
| `PATCH /tasks/{id}` with only the changed fields | `PUT /api/tasks/{id}` with the whole task | send the full task with one field changed |
| `POST /tasks/{id}/complete`, reopen with `PATCH {"completed": false}` | `PATCH /api/tasks/{id}/complete` with `{"completed": true or false}` | call only |
| `/tasks/upcoming`, `?overdue_only=true` | `?view=upcoming`, `?view=overdue` | query only |
| `?completed=true or false`, `?sort_by=` | `?status=completed or active or all`, `?sort=` | query only |
| `priority_score`, `priority_level`, `is_overdue` | `priority.exact` (and `priority.score` rounded), `priority.level`, `overdue` | the oracle checks `priority.exact` |
| errors `{"detail", "errors": [{"field", "message"}]}` | `{"error": {"message", "fields": {...}}}` | read `fields` |
| bcrypt `$2b$` | scrypt `scrypt$` | prefix only |
| deactivated user: 403 | deactivated user: 401 on API calls, 403 on login | both accepted (access refused) |
| malformed JSON: 422 | malformed JSON: 400 | both accepted (clear error, server survives) |

Two cases were added: TC-AUTH-09b (the token stops working after logout, which this build promises in FR-03) and TC-SORT-05 (tie rule on rounded scores, see SDD-02). TC-SORT-05 was also added to the Vibe Coding suite, where it passes.

## Results (19 October 2026, local run)

* Verification suite: 174 test runs, 165 passed, 9 expected failures (SDD-01 and SDD-02 below), 0 unexpected failures.
* Together with the developer's 85 tests: 250 passed, 9 expected failures, line coverage of `backend/app` 96 %. The suite alone reaches 81 %; the gap is the profile, admin and seed code, which is not in the team specification.
* Defects DEF-01, DEF-02 and DEF-03 of the Vibe Coding build do not occur here (TC-TASK-08b, TC-AUTH-04b and TC-UPC-03 pass).
* bandit: 1 medium and 4 low findings, all reviewed (see audit). pip-audit: no known vulnerability.
* Mutation check (is the suite sensitive?): 8 deliberate faults were put in the code one at a time. 7 were caught; the 8th (removing lower-casing of email in the validator) is an equivalent mutant because the repository layer lower-cases the email again.

## Findings

| ID | Requirement | Expected (team spec and decisions) | Actual (SDD build) | Type |
| --- | --- | --- | --- | --- |
| SDD-01 | FR-11, decision D1 | Remaining time rounded **up** to whole days: 2.5 days counts as 3 days (score 50), 6.5 days as 7 (25), 14.04 days as 15 (10) | Rounded **down** (spec.md clarification of 13 Oct): 75, 50 and 25 for the same deadlines | Conflict between two team decisions; 8 test runs |
| SDD-02 | FR-14, decision D2 | Higher score first; deadline only breaks a tie between equal scores | Ties are judged on the rounded score, so 78.4 (shown 78) ranks after 77.5 (shown 78) when 77.5 is due sooner; the recommendation follows the same order | Deviation; 1 test run. The Vibe Coding build passes this case |
| SDD-03 | FR-12 (spec gap 2) | 79.8 is in neither 60–79 nor 80–100 (open question to Member 1) | Level taken from the rounded score: 79.8 → 80 → Critical. The Vibe Coding build says High | Recorded difference, not a defect until the gap is closed |

## Audit notes (code review)

| ID | Where | Observation | Severity |
| --- | --- | --- | --- |
| SDD-A-01 | `db.py`, `README.md`, `spec.md` FR-25 | Main admin created with the published password `admin@123` (bandit B107). Required by the team's spec; the README asks to change it, but nothing forces it. | Medium |
| SDD-A-02 | `config.py` | Signing key from `STUDYFLOW_SECRET`, otherwise a random key stored next to the database in `data/`, which is git-ignored. No secret in the repository (unlike A-10 on the Vibe build). | Good practice |
| SDD-A-03 | `users_repo.py:52` | bandit B608 (SQL built with an f-string): the inserted text is a module constant, never user input. False positive; skipped in CI with this justification. | None |
| SDD-A-04 | `security.py` | Passwords hashed with salted scrypt; logout revokes the token; one error message for unknown email and wrong password. | Good practice |
| SDD-A-05 | `main.py` | Security headers on every response (CSP, X-Frame-Options DENY, nosniff, no-store on the API). | Good practice |
| SDD-A-06 | `config.py` | Session lasts 8 hours (Vibe Coding build: 60 minutes). The team spec does not fix a duration. | Low |
| SDD-A-07 | `frontend/js/ui.js` | Two `innerHTML` uses, both building SVG icons from constants and a server-computed number; all user text is inserted as text. Reviewed by hand; TC-SEC-08b fails if a new use appears. | None |
| SDD-A-08 | `backend/requirements.txt` | Dependencies have only lower bounds (`>=`), so a future install may pull different versions. | Low |
| SDD-A-09 | repository | No CI workflow before this suite; `.github/workflows/verification.yml` adds tests, coverage, bandit and pip-audit on every push. | Fixed by this change |
| SDD-A-10 | `docs/sdd/process-log.md` | The `specify` CLI could not be installed in the AI's sandbox; Spec Kit prompts were followed by hand. Threat to validity for the method comparison, not a code issue. | Note for the report |

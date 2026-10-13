# Research: StudyFlow SDD v1

Phase 0 output of `/speckit.plan`. Each decision lists what was chosen, why, and what
was rejected.

## R1. Web framework

- **Decision**: Starlette (ASGI) served by Uvicorn.
- **Why**: Small, well-known, async; it is the foundation FastAPI is built on, so the
  routing and request model are the same. It needs only packages that were available
  in the build environment (which had no access to the Python package index).
- **Rejected**: FastAPI (could not be installed in the build environment; its extra
  value — automatic OpenAPI — is replaced by the hand-written contract in
  `contracts/openapi.yaml`, which SDD wants anyway); Flask (synchronous, and less
  aligned with the course's earlier FastAPI version, making comparison harder).

## R2. Storage

- **Decision**: SQLite through Python's built-in `sqlite3`, one database file.
- **Why**: Zero setup for markers and teammates; meets persistence (NFR-10); the
  expected scale (a course: tens of users, hundreds of tasks) is far below SQLite's
  limits. Foreign keys and indexes give the integrity and speed needed.
- **Rejected**: PostgreSQL (used in the vibe-coded versions; needs a server or Docker,
  which slowed setup there). Trade-off recorded: SQLite allows one writer at a time,
  so a large multi-user deployment would move to PostgreSQL. All SQL sits in the
  repository modules (`users_repo.py`, `tasks_repo.py`) so that change stays local
  (information hiding, Parnas 1972).

## R3. Password hashing (NFR-03)

- **Decision**: `hashlib.scrypt` (N=2^14, r=8, p=1, 16-byte random salt, 64-byte key),
  stored as `scrypt$N$r$p$salt$hash`; comparison with `hmac.compare_digest`.
- **Why**: Memory-hard, recommended by OWASP, in the standard library (no native
  build dependency). The parameters are in the stored string, so they can be raised
  later without breaking old hashes.
- **Rejected**: bcrypt (needs a compiled package); plain SHA-256 (fast, unsuitable
  for passwords).

## R4. Sessions and sign-out (FR-03, FR-30)

- **Decision**: Signed JWT (HS256, PyJWT) with `sub`, `jti`, `exp` (8 h). Sign-out
  stores the `jti` in a `revoked_tokens` table; every request checks the token is not
  revoked and the user is still active.
- **Why**: Stateless tokens alone cannot be signed out; the small revocation table
  makes FR-03 real and lets deactivation (FR-30) take effect immediately.
- **Rejected**: Server-side session table only (equally valid; JWT keeps the API
  usable from tools like curl and matches the earlier versions).

## R5. Frontend

- **Decision**: A single-page app in plain HTML, CSS and JavaScript modules (no build
  step), served by the backend. Hash-based routing (`#/dashboard`).
- **Why**: The approved design already exists as HTML/CSS, so it carries over almost
  directly; no npm install or build is needed to run or mark the project; fewer moving
  parts for the AI to get wrong.
- **Rejected**: React + Vite (used in the vibe-coded versions; needs npm packages that
  were not available in the build environment, and a build step).

## R6. Priority as a single source (constitution II, FR-35)

- **Decision**: Only `backend/app/priority.py` knows the formula. The add-task form's
  live preview calls `POST /api/priority/preview` instead of re-implementing it.
- **Why**: Avoids two formulas drifting apart; a change to the formula is a one-module
  change.

## R7. Testing

- **Decision**: Python `unittest` (standard library) for unit and API tests, run against
  a real server started on a free port; a Playwright (Node) script for end-to-end
  checks and screenshots at 390, 768 and 1280 px. Test oracle for the formula: the
  independently written generator `seed/generate_seed.py`, whose expected scores are
  compared with the API's answers.
- **Why**: Runs with no extra packages; pytest can still discover the same tests.

## R8. Sample data

- **Decision**: `seed/seed-data.json` with deadlines stored as offsets from load time,
  so expected scores stay valid on any day; loaded with `python run.py --seed`.

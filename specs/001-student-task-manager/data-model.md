# Data Model: StudyFlow SDD v1

## users

| Column | Type | Rules |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | never reused (FR-25); 1 = main admin |
| name | TEXT NOT NULL | 1–100 chars after trim |
| email | TEXT NOT NULL UNIQUE | stored trimmed + lower-case |
| password_hash | TEXT NOT NULL | `scrypt$N$r$p$salt$hash` (NFR-03) |
| role | TEXT NOT NULL | `student` or `admin` |
| is_active | INTEGER NOT NULL DEFAULT 1 | 0 = deactivated (FR-30) |
| created_at | TEXT NOT NULL | ISO-8601 UTC |

## tasks

| Column | Type | Rules |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | |
| owner_id | INTEGER NOT NULL FK → users.id ON DELETE CASCADE | FR-21 |
| title | TEXT NOT NULL | 1–200 chars |
| subject | TEXT NOT NULL | 1–100 chars |
| deadline | TEXT NOT NULL | ISO-8601 UTC |
| difficulty | TEXT NOT NULL | Easy / Medium / Hard / Very Hard |
| estimated_hours | REAL NOT NULL | 0 < h ≤ 1000 |
| completed | INTEGER NOT NULL DEFAULT 0 | |
| completed_at | TEXT NULL | set when completed, cleared when reopened |
| created_at | TEXT NOT NULL | |
| updated_at | TEXT NOT NULL | |

Indexes: `tasks(owner_id, completed)`, `tasks(owner_id, deadline)`.

Priority is **not stored**; it is derived on read (FR-13).

## revoked_tokens

| Column | Type | Rules |
|---|---|---|
| jti | TEXT PK | token ID from the JWT |
| expires_at | TEXT NOT NULL | rows past expiry are purged on startup |

## Derived values (not stored)

- `overdue` = not completed and deadline < now (FR-18)
- `priority` = `{score, exact, level, days_left, deadline_score, difficulty_score,
  time_score, deadline_part, difficulty_part, time_part}`, or `null` when completed

## State transitions

- Task: `active` ⇄ `completed` (FR-08). Delete is final (FR-07).
- User: `active` ⇄ `deactivated` (FR-30); main admin is always active.

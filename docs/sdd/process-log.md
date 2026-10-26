# SDD process log — StudyFlow SDD v1

Raw material for the report (sections 4.x and 7.x): what was done at each Spec-Kit
step, what came out, and what went wrong. Newest entries at the bottom.

## 2026-10-12 — Design before spec

- UI designed first as a clickable mockup (8 screens, light/dark, responsive) and
  approved by Niladri; sample data file created with expected scores.

## 2026-10-13 — Setup

- Spec-Kit (github/spec-kit, commit 6c62e10) templates and scripts copied into
  `.specify/`. The `specify` CLI itself could not be installed in the AI's build
  sandbox (no access to the Python package index), so each command's prompt
  (`.specify/upstream-commands/*.md`) was followed by hand. Teammates can run
  `specify init --here --integration claude` locally to get the slash commands.
- **Threat to validity**: the build sandbox also had no npm access. This forced
  technology choices (Starlette instead of FastAPI, plain JS instead of React) that
  differ from the vibe-coded versions. Recorded in research.md.

## /speckit.constitution

- Six principles; the priority formula is locked in one module (principle II).

## /speckit.specify + /speckit.clarify

- Official FR-01–FR-21 kept with the same IDs; FR-22–FR-35 added for profile, admin
  and interface.
- Clarify found three gaps in the official priority table that Niladri decided:
  1. Deadline bands have gaps (2–3, 6–7, 14–15 days) → count whole days left.
  2. Is the level from the rounded or exact score? → rounded (shown) score.
  3. Upcoming window not defined → 7 days.
  These are exactly the kind of gaps that, in the vibe-coded build, the AI filled
  silently (compare ISSUE-001).
- Six smaller defaults chosen by the AI and marked "team to confirm" in the spec.

## /speckit.checklist

- Requirements checklist passes after clarification.

## /speckit.plan

- research.md records 8 decisions with rejected alternatives; STRIDE pass in plan.md.

## /speckit.tasks + /speckit.analyze

- 42 tasks by user story; analyze found 2 medium issues (NFR-02 had no task; FR-30
  did not cover role changes). Both fixed in the spec/tasks before any code.

## /speckit.implement — backend

- Priority tests written first and run red (module missing), then `priority.py`;
  18/18 green.
- Plan amended: Pydantic dropped (hand-written validators give the exact messages
  FR-10 asks for). Plan updated in the same commit.
- First full test run: 85 tests, 3 failures. Causes:
  1. **Test bug** — overview test shared a database with another test in the same
     class; totals were off. Fixed by giving it its own class.
  2. **Spec gap** — admin search "5" also matched emails containing 5. Spec said
     "searchable by ID" without saying how. Clarification added to spec.md, then code.
  3. **Test timing** — an "exactly 24 h" deadline sent through the API arrives as
     23.9999 h because the server reads the clock later. Exact boundaries stay in the
     unit tests (fixed clock); API edge tests add one minute.
- Contract corrected (wrong current password → 422, not 401) — found while writing
  profile tests; spec clarification added.
- Result: 85/85 backend tests pass.

## /speckit.implement — frontend and verification

- Frontend built from the approved design as plain JavaScript modules; user data is
  inserted as text only (no innerHTML), and the server sends a strict
  Content-Security-Policy.
- First browser run: 63/66 checks. All three failures were in the **test script**,
  not the app: (1) admin totals were checked after the script itself had added a
  student; (2) the selector "Activate" also matched the "Deactivate" button;
  (3) a search result was read before the 250 ms search delay had passed.
- Visual review of the screenshots found two real UI defects, fixed: the admin
  priority bars were all one colour (a CSS specificity bug), and the score-scale
  labels on the task form were evenly spaced instead of at 40/60/80.
- A flaky check (Upcoming count read before the list loaded) was fixed by waiting for
  the list itself.
- Final: 85/85 backend tests, 66/66 browser checks on fresh sample data. Dashboard
  ready in ≈0.8 s including sign-in (NFR-02).
- Open: NFR-14 human review (`docs/sdd/review-log.md`); an automated accessibility
  scan was not run.

## 2026-10-26 — GitHub issues #1 and #2 (found by Khadija's independent verification)

Both issues came from `/speckit.clarify` answers of 13 Oct that contradicted team
decisions Zahra (specification owner) had already recorded on 10 Oct. Fixed spec first,
then code and tests; nothing else changed in behaviour.

| Issue | Was | Now |
|---|---|---|
| #1 SDD-01, FR-11, decision D1 | whole days counted *down*: 2.5 days → 75, 6.5 days → 50, 14 days + 1 min → 25 | time left rounded *up*: 2.5 days → 3 → 50, 6.5 → 7 → 25, 14 days + 1 min → 15 → 10; under 24 h still 100 |
| #2 SDD-02, FR-14, decision D2 | ties judged on the shown whole-number score, so 77.5 (due sooner) ranked above 78.4 | ordering uses the exact score; the deadline only breaks a tie between equal exact scores. The whole-number score is still what the UI shows |

Changed: `spec.md` (priority table, FR-14, edge cases, clarifications), `contracts/openapi.yaml`
(descriptions), `backend/app/priority.py`, explanation texts in three frontend views,
`seed/generate_seed.py` (oracle), developer tests, and the two strict-xfail markers in
`backend/verification/` (the defects they tracked are fixed).

Evidence:
- Before updating tests, 8 developer tests failed — exactly the old round-down and
  shown-score tie expectations — and Khadija's 9 strict-xfail cases reported XPASS,
  i.e. her suite confirmed both fixes independently.
- After: developer tests 86/86; Khadija's suite 174/174 with no markers; CI command
  (`pytest backend/tests backend/verification`) 260 passed; browser checks 66/66 on fresh
  sample data. API response times unchanged (about 2 ms for dashboard and task list,
  same as before the change).
- No sample task changed score or level; only the two in-between edge cases did.

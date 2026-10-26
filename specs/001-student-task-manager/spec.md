# Feature Specification: StudyFlow — Smart Student Task Manager (SDD v1)

**Feature Branch**: `001-student-task-manager`

**Created**: 2026-10-13

**Status**: Clarified (ready for planning)

**Input**: The team's official requirements (`Project_Idea_Smart_Student_Task_Manager.pdf`:
FR-01–FR-21, NFR-01–NFR-14 and the locked priority formula), plus the student profile
and admin panel the team asked for on 2026-10-12, and the approved SDD v1 UI design.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Create an account and sign in (Priority: P1)

A student registers with name, email and password, signs in, and signs out. Their
tasks are still there the next time they sign in.

**Why this priority**: Nothing else works without an identity; it also carries the
security requirements.

**Independent Test**: Register, sign out, sign in again, reach the dashboard.

**Acceptance Scenarios**:

1. **Given** no account for `a@b.fi`, **When** the student registers with name "Aino",
   email `a@b.fi` and an 8+ character password, **Then** an account is created and the
   student is signed in.
2. **Given** an account for `a@b.fi`, **When** someone registers again with `A@B.fi`,
   **Then** registration is refused with "An account with this email already exists."
3. **Given** a registered student, **When** they sign in with the wrong password,
   **Then** they see "Email or password is incorrect." and are not signed in.
4. **Given** a signed-in student, **When** they sign out, **Then** their session token
   no longer works, even if someone kept a copy.
5. **Given** a student who created tasks, **When** they sign out and back in,
   **Then** the same tasks are shown.

---

### User Story 2 — Manage tasks (Priority: P1)

A student adds assignments, exams and projects with title, subject, deadline,
difficulty and estimated hours; views, edits, deletes and completes them.

**Why this priority**: It is the core of the product.

**Independent Test**: Create a task, edit its deadline, mark it complete, delete it.

**Acceptance Scenarios**:

1. **Given** a signed-in student, **When** they save a task with all five fields valid,
   **Then** it appears in their task list with a priority score and level.
2. **Given** the add-task form, **When** the title is empty, **Then** the task is not
   saved and the form says "Title can't be empty."
3. **Given** the add-task form, **When** estimated hours is 0 or negative, **Then** the
   task is not saved and the form says "Estimated hours must be more than 0."
4. **Given** an incomplete task, **When** the student marks it complete, **Then** it
   shows as completed and leaves the active list; they can mark it incomplete again.
5. **Given** a task, **When** the student deletes it and confirms, **Then** it is gone
   for good.

---

### User Story 3 — See priorities and a recommendation (Priority: P1)

Each incomplete task gets a score from 0 to 100 and a level. The dashboard answers
"What should I work on today?" with the highest-priority incomplete task and explains
the score.

**Why this priority**: It is what makes the product "smart".

**Independent Test**: Create three tasks with known inputs; check scores, levels, order
and the recommendation against the formula.

**Acceptance Scenarios**:

1. **Given** a task due in 14.5 hours, Hard, 8 hours, **Then** its score is 90, Critical
   (deadline 100×0.5 + 80×0.3 + 80×0.2).
2. **Given** a task due in 60 hours (2.5 days), **Then** its deadline score is 50
   (time left rounded up to 3 days, team decision D1).
3. **Given** two incomplete tasks with the same exact score (75), **Then** the one with
   the earlier deadline is listed first. A higher exact score always comes first, even
   when both show the same whole number (78.4 before 77.5).
4. **Given** a task whose deadline, difficulty or hours change, **Then** its score and
   level are recalculated immediately.
5. **Given** incomplete tasks, **Then** the recommendation is the first task in priority
   order, shown with its deadline, difficulty and time contributions.
6. **Given** no incomplete tasks, **Then** the recommendation says there is nothing left
   to do.

---

### User Story 4 — Organise tasks (Priority: P2)

The student filters by subject and completion status, sorts by priority or deadline,
and sees upcoming and overdue tasks.

**Independent Test**: With mixed tasks, apply each filter and sort and check the result.

**Acceptance Scenarios**:

1. **Given** tasks in two subjects, **When** filtering by one subject, **Then** only that
   subject's tasks are listed.
2. **Given** completed and incomplete tasks, **When** filtering "Completed", **Then** only
   completed tasks are listed.
3. **Given** tasks, **When** sorting by deadline, **Then** they are ordered earliest first.
4. **Given** an incomplete task whose deadline has passed, **Then** it is marked overdue
   and appears in the Overdue view. A completed task is never overdue.
5. **Given** incomplete tasks due in 2 days and in 9 days, **Then** only the first appears
   in Upcoming (next 7 days).

---

### User Story 5 — Dashboard (Priority: P2)

On sign-in the student sees counts of incomplete, completed, high-priority and overdue
tasks, the recommendation, upcoming deadlines and the priority mix.

**Independent Test**: Load the sample data and compare dashboard numbers with the data.

**Acceptance Scenarios**:

1. **Given** the sample student Niladri (ID 2), **Then** the dashboard shows 13
   incomplete, 4 completed, 6 high priority (1 Critical + 5 High), 1 overdue, and
   recommends "Security lab: STRIDE threat model" (90).

---

### User Story 6 — Student profile (Priority: P3)

A user sees their account details and can change their email and password.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **Then** the profile shows user ID, name, email, role,
   joined date, task count and completed count.
2. **Given** the change-email form, **When** the new email equals the current one, is
   invalid, or belongs to another account, **Then** the change is refused with a clear
   message. A correct current password is required.
3. **Given** the change-password form, **When** the new password equals the current
   password, is shorter than 8 characters, or the confirmation does not match, **Then**
   the change is refused. A correct current password is required.
4. **Given** a successful password change, **Then** the old password no longer works.

---

### User Story 7 — Admin panel (Priority: P3)

An admin sees platform statistics, manages users and views all tasks.

**Acceptance Scenarios**:

1. **Given** a fresh installation, **Then** a main admin exists with user ID 1, email
   `admin123@gmail.com` and initial password `admin@123`.
2. **Given** a student, **When** they call any admin function, **Then** they get 403.
3. **Given** an admin, **When** they deactivate a student, **Then** that student cannot
   sign in and their existing session stops working; their tasks are kept.
4. **Given** an admin, **When** they try to deactivate or demote the main admin or
   themselves, **Then** the action is refused.
5. **Given** an admin, **When** they open All tasks and filter by a student, **Then**
   only that student's open tasks are listed, in priority order.

---

### User Story 8 — Comfortable to use anywhere (Priority: P2)

The interface works in light and dark mode and on phone, tablet and desktop screens.

**Acceptance Scenarios**:

1. **Given** any page, **When** the user switches theme, **Then** the whole interface
   changes instantly and the choice is remembered in that browser.
2. **Given** a window narrower than 600 px, **Then** navigation moves to a bottom bar,
   lists become stacked cards and nothing needs horizontal scrolling.

---

### Edge Cases

- Deadline 23 h 59 min away → less than 24 hours → 100. Exactly 24 h → 1 day → 75.
- Deadline 60 h away → rounded up to 3 days → 50. 156 h → 7 days → 25.
- Deadline exactly 14 days away → 25; 14 days and 1 minute → rounded up to 15 → 10.
- Score 79.5 → shown as 80 → Critical (level follows the shown score).
- Estimated hours 12 → time score capped at 100.
- Email entered with capitals or spaces → trimmed and compared case-insensitively.
- A student asks for a task ID that belongs to someone else → "Task not found" (404).
- Deadline in the past at creation → allowed; the task is immediately overdue.
- Last active admin → cannot be deactivated or demoted.

## Requirements *(mandatory)*

IDs FR-01–FR-21 keep the numbering of the team's official requirements document.

### Functional Requirements

**Account**

- **FR-01**: Users MUST be able to register with name (1–100 characters), email (valid
  format, unique ignoring case) and password (at least 8 characters).
- **FR-02**: Registered, active users MUST be able to sign in with email and password.
- **FR-03**: Users MUST be able to sign out; the signed-out session token MUST stop working.

**Tasks**

- **FR-04**: Students MUST be able to create tasks.
- **FR-05**: Each task MUST have title, subject, deadline (date and time), difficulty
  (Easy, Medium, Hard, Very Hard) and estimated hours.
- **FR-06**: Students MUST be able to edit their own tasks.
- **FR-07**: Students MUST be able to delete their own tasks, after confirming.
- **FR-08**: Students MUST be able to mark a task complete and mark it incomplete again.
- **FR-09**: Students MUST be able to view a task's details, including its score
  breakdown when incomplete.
- **FR-10**: The system MUST reject a task unless: title is non-empty (≤ 200 characters);
  subject is non-empty (≤ 100 characters); deadline is a valid date-time; estimated
  hours is a number greater than 0 and at most 1000; difficulty is one of the four
  levels. Each failure MUST name the field and the problem.

**Priority** (see "Priority Calculation" below)

- **FR-11**: The system MUST calculate a priority score for every incomplete task.
- **FR-12**: The system MUST classify each score as Critical, High, Medium or Low.
- **FR-13**: Scores MUST reflect the current deadline, difficulty and hours, and the
  current time, whenever they are shown.
- **FR-14**: Priority order MUST be: exact score highest first; equal exact scores →
  earlier deadline first; still equal → earlier created first (team decision D2).
  The shown whole-number score is for display only.

**Organisation**

- **FR-15**: Students MUST be able to filter tasks by subject and by status (active,
  completed, all), and search by title.
- **FR-16**: Students MUST be able to sort tasks by priority or by deadline.
- **FR-17**: The system MUST show upcoming tasks: incomplete, not overdue, due within
  the next 7 days, earliest first.
- **FR-18**: The system MUST mark incomplete tasks whose deadline has passed as overdue.

**Dashboard and recommendation**

- **FR-19**: The dashboard MUST show counts of incomplete, completed, high-priority
  (High or Critical) and overdue tasks, tasks due within 7 days, completion percentage,
  priority mix, and the upcoming list.
- **FR-20**: The dashboard MUST recommend the first incomplete task in priority order
  as "What should I work on today?", with its score breakdown.

**Security and access**

- **FR-21**: Students MUST only be able to see and change their own tasks. Another
  user's task MUST be indistinguishable from a missing one.

**Profile** (added 2026-10-12)

- **FR-22**: Users MUST be able to view their profile: user ID, name, email, role,
  joined date, number of tasks, number completed.
- **FR-23**: Users MUST be able to change their email after giving their current
  password. The new email MUST be valid, different from the current one and not used
  by another account.
- **FR-24**: Users MUST be able to change their password after giving their current
  password. The new password MUST be at least 8 characters, different from the current
  password, and typed twice identically.
- **FR-25**: Every user MUST have a unique numeric user ID that is never reused.

**Admin** (added 2026-10-12)

- **FR-26**: The system MUST have two roles, student and admin. A main admin with user
  ID 1, email `admin123@gmail.com` and initial password `admin@123` MUST exist after
  first start; its email and admin role cannot be changed and it cannot be deactivated.
- **FR-27**: Admins MUST see an overview: number of students (active / deactivated),
  number of tasks (open / completed), completion rate, open Critical tasks, overdue
  tasks and students affected, tasks created and completed per day for the last 14
  days, open tasks per priority level, top subjects, and students with overdue tasks.
- **FR-28**: Admins MUST see a list of users with ID, name, email, role, status and
  open / completed / overdue counts, searchable by name, email or ID.
- **FR-29**: Admins MUST be able to create a user (name, email, password, role).
- **FR-30**: Admins MUST be able to deactivate and reactivate users. Deactivated users
  cannot sign in and their sessions stop working; their data is kept. Admins can also
  change a user's role. An admin cannot deactivate or change the role of the main admin
  or of themselves, so at least one active admin always remains.
- **FR-31**: Admins MUST be able to list all open tasks across users in priority order,
  filtered by priority level and by student.
- **FR-32**: Admin functions MUST be refused (403) for non-admin users.

**Interface** (from the approved design)

- **FR-33**: The interface MUST offer light and dark themes, default to the device
  setting, and remember the user's choice in that browser.
- **FR-34**: The interface MUST adapt to the window: sidebar on desktop, top bar on
  tablet (≤ 960 px), bottom tab bar and stacked cards on phones (≤ 600 px).
- **FR-35**: The add/edit form MUST show a live priority preview computed by the same
  formula the server uses.

### Non-Functional Requirements

- **NFR-01**: API responses within 2 s under normal use.
- **NFR-02**: Main pages load within 2 s under normal network conditions.
- **NFR-03**: Passwords are never stored or logged in plain text; only salted slow hashes.
- **NFR-04**: Only authenticated users reach task, profile and admin functions.
- **NFR-05**: A user cannot view, modify or delete another user's tasks.
- **NFR-06**: All input is validated on the server before it is stored or processed.
- **NFR-07**: Labels are clear and error messages say what to fix.
- **NFR-08**: Responsive on desktop and mobile.
- **NFR-09**: Creating a task takes one short form.
- **NFR-10**: Data persists across sign-out, sign-in and server restarts.
- **NFR-11**: Failed operations show an error message; the UI never fails silently.
- **NFR-12**: Create/update with missing or invalid data is rejected and nothing is saved.
- **NFR-13**: Authentication, tasks, priority, dashboard, recommendation, profile and
  admin are separate modules.
- **NFR-14**: AI-generated code is reviewed by at least one team member before it is
  considered complete.
- **NFR-15**: No decorative animation; theme changes and navigation are instant.
- **NFR-16**: Text meets WCAG AA contrast in both themes; all controls are reachable by
  keyboard and have accessible names.

### Priority Calculation (locked — do not change)

`Priority score = Deadline score × 0.50 + Difficulty score × 0.30 + Time score × 0.20`

**Deadline score** — less than 24 hours left (or overdue) scores 100; otherwise the time
left is rounded **up** to whole days, `days = ceil(hours until deadline ÷ 24)`
(team decision D1, issue #1):

| Situation | Score |
|---|---|
| Deadline passed (overdue) | 100 |
| Less than 24 hours | 100 |
| 1–2 days | 75 |
| 3–6 days | 50 |
| 7–14 days | 25 |
| More than 14 days (15 or more after rounding up) | 10 |

**Difficulty score**: Easy 20, Medium 50, Hard 80, Very Hard 100.

**Time score**: `min(estimated hours × 10, 100)`.

**Shown score**: the exact score rounded half up to a whole number (73.5 → 74).

**Level** (from the shown score): 80–100 Critical, 60–79 High, 40–59 Medium, 0–39 Low.

Completed tasks have no score and show "Done".

### Key Entities

- **User**: numeric ID, name, email, role (student/admin), active flag, password hash,
  joined date.
- **Task**: numeric ID, owner (a user), title, subject, deadline, difficulty,
  estimated hours, completed flag, created time, completed time.
- **Revoked session**: identifies a signed-out session token until it would have expired.

## Success Criteria *(mandatory)*

- **SC-001**: For all 30 open tasks in the sample data, the shown score and level equal
  the values computed independently from this spec (100% match).
- **SC-002**: A new student can register and save a first task in under 2 minutes.
- **SC-003**: Every functional requirement is covered by at least one passing automated
  test.
- **SC-004**: No request by a student returns or changes another user's task (all
  isolation tests pass).
- **SC-005**: All pages are usable at 390 px, 768 px and 1280 px wide without
  horizontal scrolling.
- **SC-006**: API responses for the sample data set are under 2 s (measured).

## Clarifications

### Session 2026-10-13 (decided by the team — Niladri)

- Q: The deadline table jumps from "1–2 days" to "3–6 days" (and 6 → 7, 14 → more than
  14). Which band does 2.5 days or 6.5 days fall in? → A (corrected 2026-10-26, issue #1):
  Zahra's team decision D1 of 10 Oct applies — round the time left **up** to whole
  days: 2.5 days → 3 → 50; 6.5 days → 7 → 25; 14 days and a minute → 15 → 10. The first
  answer (count down, given on 13 Oct) contradicted D1, which had not been checked.
- Q: Is the level decided from the shown (rounded) score or the exact score?
  → A: From the shown score, rounded half up. 79.5 → 80 → Critical.
- Q: How far ahead does "Upcoming" look? → A: The next 7 days.

### Session 2026-10-13 (defaults chosen while specifying — team to confirm)

- Q: Is a completed task past its deadline overdue? → A: No. FR-18 says incomplete
  tasks only.
- Q: What counts as a tie in FR-14? → A (corrected 2026-10-26, issue #2, team decision
  D2): equal **exact** score; then earlier deadline; then earlier creation. The first
  answer (equal shown score) let 77.5 rank above 78.4.
- Q: May a deadline be in the past when a task is created? → A: Yes; it is
  immediately overdue (students log late work too).
- Q: Can estimated hours be a decimal? → A: Yes, greater than 0 and at most 1000.
- Q: Are overdue tasks eligible for the recommendation? → A: Yes; they are incomplete
  and usually the most urgent.
- Q: Which time zone is used? → A: Stored in UTC, entered and shown in the browser's
  local time; "hours until deadline" is the real time difference.

### Session 2026-10-13 (found during implementation — spec updated first)

- Q: In the admin user search (FR-28), does "5" match emails containing a 5?
  → A: No. A search that is only a number (optionally with #) matches the user ID
  exactly; anything else matches name or email.
- Q: What status does a wrong *current* password get when changing email or password?
  → A: 422 with a field message, like other form errors (401 would sign the user out
  in the UI). The main admin's email change is refused with 403 (FR-26).

## Assumptions

- One deployment serves a small group (a course): tens of users, hundreds of tasks.
- Users have a modern browser (last two versions of Chrome, Firefox, Safari, Edge).
- Email addresses are not verified by sending mail (out of scope).
- Out of scope: password reset by email, notifications, task sharing, attachments,
  recurring tasks, calendar sync, multiple languages.

# Traceability matrix — StudyFlow SDD v1

Requirement → where it is built → how it is checked → result (2026-10-13).
Backend tests: `python -m unittest discover -s backend/tests -t .` (85 tests, all pass).
Browser checks: `node e2e/e2e.mjs` on freshly seeded data (66 checks, all pass; log in
`e2e-results.txt`).

| Req | Built in | Automated check(s) | Result |
|---|---|---|---|
| FR-01 Register | `routes/auth.py`, `validation.py`, `views/login.js` | `test_auth.Register.*`; E2E "FR-01 …" | Pass |
| FR-02 Sign in | `routes/auth.py` | `test_auth.Login.*`; E2E login steps | Pass |
| FR-03 Sign out revokes | `security.revoke`, `routes/auth.py` | `test_auth.Sessions.test_logout_revokes_token`; E2E "FR-03" | Pass |
| FR-04 Create task | `routes/tasks.py`, `tasks_repo.create`, `views/task-form.js` | `test_tasks.CreateAndView.*`; E2E "FR-04" | Pass |
| FR-05 Task fields | `db.py` schema, `validation.task` | `test_tasks.CreateAndView.*` | Pass |
| FR-06 Edit own task | `routes/tasks.update_task` | `test_tasks.EditCompleteDelete.test_edit_recalculates_priority` | Pass |
| FR-07 Delete own task | `routes/tasks.delete_task`, confirm dialog in `ui.js` | `test_tasks.EditCompleteDelete.test_delete` | Pass |
| FR-08 Complete / reopen | `routes/tasks.complete_task` | `test_tasks.EditCompleteDelete.test_complete_and_reopen`; E2E "FR-08" | Pass |
| FR-09 View details | `routes/tasks.get_task`, `views/task-detail.js` | `test_tasks.CreateAndView.test_view_details_has_breakdown`; E2E "FR-09" | Pass |
| FR-10 Validation | `validation.py` | `test_tasks.Validation.*` (8 tests); E2E "FR-10" | Pass |
| FR-11 Score | `priority.score` | `test_priority.Components.*`; `test_seed_oracle` (30 tasks) | Pass |
| FR-12 Levels | `priority.classify` | `test_priority.RoundingAndLevels.*` | Pass |
| FR-13 Recalculate | scores computed on read (`tasks_repo.to_dict`) | `test_tasks…test_edit_recalculates_priority` | Pass |
| FR-14 Tie-break | `priority.sort_key` | `test_priority.Ordering.*`; `test_dashboard…tie_breaks_on_deadline` | Pass |
| FR-15 Filter / search | `routes/tasks.list_tasks`, `views/tasks.js` | `test_tasks.Organise.test_filter_*`, `test_search_title`; E2E "FR-15" | Pass |
| FR-16 Sort | `tasks_repo.sort_by_*` | `test_tasks.Organise.test_sort_*`; E2E "FR-16" | Pass |
| FR-17 Upcoming (7 days) | `recommendation.upcoming` | `test_tasks.Organise.test_upcoming…`; E2E "FR-17" | Pass |
| FR-18 Overdue | `tasks_repo.to_dict`, `recommendation.overdue` | `test_tasks.Organise.test_overdue_excludes_completed` | Pass |
| FR-19 Dashboard | `recommendation.summary`, `views/dashboard.js` | `test_dashboard.*`; `test_seed_oracle…us5`; E2E "US5" | Pass |
| FR-20 Recommendation | `recommendation.recommend` | `test_dashboard.*`; E2E "FR-20" | Pass |
| FR-21 Isolation | owner filter in every `tasks_repo` student function | `test_isolation.*`; E2E "FR-21" | Pass |
| FR-22 Profile | `routes/profile.me`, `views/profile.js` | `test_profile.Profile.*`; E2E "FR-22" | Pass |
| FR-23 Change email | `routes/profile.change_email` | `test_profile.ChangeEmail.*` | Pass |
| FR-24 Change password | `routes/profile.change_password` | `test_profile.ChangePassword.*`; E2E "FR-24" | Pass |
| FR-25 Numeric unique IDs | `AUTOINCREMENT` in `db.py` | `test_profile.Profile.test_user_ids_are_unique_increasing_numbers` | Pass |
| FR-26 Roles, main admin | `db.init_db`, `routes/admin.update_user` | `test_admin.Access.test_main_admin_bootstrapped_as_user_1`; E2E "FR-26" | Pass |
| FR-27 Admin overview | `routes/admin.overview` | `test_admin.Overview.*`; `test_seed_oracle…admin_overview`; E2E "FR-27" | Pass |
| FR-28 User list / search | `routes/admin.list_users` | `test_admin.Users.test_list_and_search` | Pass |
| FR-29 Create user | `routes/admin.create_user` | `test_admin.Users.test_create_user` | Pass |
| FR-30 (De)activate, roles | `routes/admin.update_user`, `security.require_user` | `test_admin.Users.test_deactivate…`, `test_main_admin_and_self…`, `test_change_role`; E2E "FR-30" | Pass |
| FR-31 All tasks | `routes/admin.all_tasks` | `test_admin.Tasks.*`; E2E "FR-31" | Pass |
| FR-32 Admin-only | `security.require_admin` | `test_admin.Access.test_students_get_403_everywhere`; E2E "FR-32" | Pass |
| FR-33 Themes | `theme-init.js`, `app.js`, `app.css` | E2E "FR-33" | Pass |
| FR-34 Responsive | `app.css` breakpoints | E2E "FR-34 …" at 390 / 768 / 1280 px (26 checks) | Pass |
| FR-35 Live preview | `routes/tasks.preview`, `views/task-form.js` | `test_tasks.Preview.*`; E2E "FR-35" | Pass |
| NFR-01 API < 2 s | — | `test_seed_oracle…api_response_times_under_2_seconds` | Pass |
| NFR-02 Page < 2 s | — | E2E "NFR-02" (≈0.8 s incl. sign-in) | Pass |
| NFR-03 Hashed passwords | `security.hash_password` (scrypt) | `test_auth.Register.test_password_is_stored_hashed` | Pass |
| NFR-04 Auth required | `security.require_user` | `test_auth.Sessions.test_protected_endpoints_need_a_token` | Pass |
| NFR-05 Data isolation | as FR-21 | `test_isolation.*` | Pass |
| NFR-06 Server validation | `validation.py` | `test_tasks.Validation.*`, `test_auth…bad_json` | Pass |
| NFR-07 Clear messages | `validation.py`, `showFieldErrors` | message text asserted in tests | Pass |
| NFR-08 Responsive | as FR-34 | E2E | Pass |
| NFR-09 Short task form | `views/task-form.js` (5 fields) | E2E task creation | Pass |
| NFR-10 Persistence | SQLite file | `test_auth.Sessions.test_tasks_persist_across_sign_out_and_in` | Pass |
| NFR-11 Errors shown | `api.js`, toasts | E2E "no JavaScript errors" + manual | Pass |
| NFR-12 Reject invalid, save nothing | `validation.py` before writes | `test_tasks.Validation.post_invalid` (asserts empty list) | Pass |
| NFR-13 Modular | one module per area (see plan.md) | code review | Pass |
| NFR-14 Human review | `docs/sdd/review-log.md` | **team action — open** | Open |
| NFR-15 No animation | `app.css` has no transitions/animations | code review | Pass |
| NFR-16 Contrast / keyboard | tokens from approved design; real buttons/labels, radiogroup keys | code review (no automated a11y scan) | Partly verified |

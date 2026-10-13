# Quickstart: StudyFlow SDD v1

## Run

```bash
python -m pip install -r backend/requirements.txt
python run.py --seed        # first time: creates data/studyflow.db with sample data
# open http://127.0.0.1:8000
```

`python run.py` starts without touching data; `python run.py --reset --seed` starts over.

## Sample accounts

| Who | Email | Password |
|---|---|---|
| Main admin (ID 1) | admin123@gmail.com | admin@123 |
| Student (ID 2, 17 tasks) | niladri@student.test | Student@123 |
| Students 3–6 | zahra@ / khadija@ / aino@ / mikael@student.test | Student@123 |
| Deactivated (ID 7) | sara@student.test | cannot sign in |

Change the admin password from Profile before anyone else can reach the app.

## Validate against the spec

```bash
python -m unittest discover -s backend/tests -t . -v     # unit + API tests
python run.py --reset --seed --port 8765 &               # server for E2E
node e2e/e2e.mjs http://127.0.0.1:8765                   # browser run-through
```

Manual check (US5): sign in as Niladri → dashboard shows 13 incomplete, 4 completed,
6 high priority, 1 overdue, recommendation "Security lab: STRIDE threat model" (90).

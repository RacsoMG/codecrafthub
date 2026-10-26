# CodeCraftHub

A simple personalized learning platform for developers. CodeCraftHub is a small **REST API** built with **Python + Flask** that lets you keep track of the courses you want to learn: what each course is about, when you want to finish it, and how far along you are.

It is designed for people learning REST APIs for the first time: there is **no database** (data lives in a plain `courses.json` file) and **no login**.

---

## 1. Features

- Add, list, view, update and delete courses (full **CRUD**)
- Each course has a name, description, target date and status
- Status is limited to `Not Started`, `In Progress` or `Completed`
- Dates are checked to be real dates in `YYYY-MM-DD` format
- Data is stored in `courses.json`, created automatically on first run
- Clear JSON error messages (missing fields, bad values, course not found, file errors)
- **Bonus:** `GET /api/courses/stats` endpoint with course counts by status
- Automated tests (`pytest`) and a curl test script

## 2. Project structure

```
codecrafthub/
├── app.py            # The whole Flask application (routes, validation, storage)
├── courses.json      # Your data (created automatically - do not need to create it)
├── requirements.txt  # Python packages the project needs
├── test_app.py       # Automated tests (run with pytest)
├── test_api.sh       # curl tests against the running server
├── PROMPTS.md        # The GenAI prompts used to build the project
└── README.md         # This file
```

Inside `app.py` the code is split into sections:

| Section | What it does |
|---|---|
| Configuration | Path of the JSON file, list of valid statuses, required fields |
| Storage helpers | `load_courses()`, `save_courses()`, `get_next_id()`, `find_course()` |
| Validation helpers | `get_json_body()`, `validate_fields()` |
| API endpoints | One function per route |
| Error handlers | Make sure every error is returned as JSON |

## 3. Installation

You need **Python 3.9 or newer**. Check with `python --version` (or `python3 --version`).

1. Get the code (clone your repository or unzip the project) and enter the folder:
   ```bash
   cd codecrafthub
   ```
2. *(Recommended)* create and activate a virtual environment:
   ```bash
   python -m venv venv
   # macOS / Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 4. Running the application

```bash
python app.py
```

You should see:

```
CodeCraftHub API is starting...
Data will be stored in: /path/to/codecrafthub/courses.json
API will be available at: http://localhost:5000
```

Leave this terminal open. Open `http://localhost:5000` in a browser to see the list of endpoints. Stop the server with **Ctrl + C**.

## 5. API endpoints

All requests and responses use JSON. For `POST` and `PUT` always send the header `Content-Type: application/json`.

| Method | URL | What it does | Success code |
|---|---|---|---|
| POST | `/api/courses` | Add a new course | 201 |
| GET | `/api/courses` | Get all courses | 200 |
| GET | `/api/courses/<id>` | Get one course | 200 |
| PUT | `/api/courses/<id>` | Update a course | 200 |
| DELETE | `/api/courses/<id>` | Delete a course | 200 |
| GET | `/api/courses/stats` | Statistics by status (bonus) | 200 |

### Course fields

| Field | Type | Rules |
|---|---|---|
| `id` | integer | Generated automatically, starts at 1 |
| `name` | string | Required, not empty |
| `description` | string | Required, not empty |
| `target_date` | string | Required, real date in `YYYY-MM-DD` |
| `status` | string | Required, one of `Not Started`, `In Progress`, `Completed` |
| `created_at` | string | Generated automatically |
| `updated_at` | string | Added automatically after an update |

### Add a course — `POST /api/courses`

```bash
curl -X POST http://localhost:5000/api/courses \
  -H "Content-Type: application/json" \
  -d '{"name": "Python Basics", "description": "Learn Python fundamentals", "target_date": "2026-12-31", "status": "Not Started"}'
```

Response `201 Created`:

```json
{
  "success": true,
  "message": "Course added successfully",
  "course": {
    "id": 1,
    "name": "Python Basics",
    "description": "Learn Python fundamentals",
    "target_date": "2026-12-31",
    "status": "Not Started",
    "created_at": "2026-10-26 10:30:00"
  }
}
```

### Get all courses — `GET /api/courses`

```bash
curl http://localhost:5000/api/courses
```

Response `200 OK`:

```json
{ "success": true, "count": 1, "courses": [ { "id": 1, "name": "Python Basics", "...": "..." } ] }
```

### Get one course — `GET /api/courses/<id>`

```bash
curl http://localhost:5000/api/courses/1
```

### Update a course — `PUT /api/courses/<id>`

Send only the fields you want to change:

```bash
curl -X PUT http://localhost:5000/api/courses/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress"}'
```

### Delete a course — `DELETE /api/courses/<id>`

```bash
curl -X DELETE http://localhost:5000/api/courses/1
```

Response `200 OK` includes the `deleted_course`.

### Statistics (bonus) — `GET /api/courses/stats`

```bash
curl http://localhost:5000/api/courses/stats
```

```json
{
  "success": true,
  "stats": {
    "total_courses": 3,
    "by_status": { "Not Started": 1, "In Progress": 1, "Completed": 1 }
  }
}
```

### Errors

Every error has the same shape: `{"success": false, "error": "<message>"}`.

| Situation | Code | Example message |
|---|---|---|
| Missing fields | 400 | `Missing required field(s): description, target_date, status` |
| Bad status | 400 | `'status' must be one of: Not Started, In Progress, Completed` |
| Bad date | 400 | `'target_date' must be a valid date in YYYY-MM-DD format` |
| Body is not JSON | 400 | `Request body must be a JSON object ...` |
| Course does not exist | 404 | `Course with id 999 not found` |
| `courses.json` unreadable / corrupted | 500 | `Data file is corrupted (invalid JSON): ...` |

## 6. Testing

### Option A — automated tests (no server needed)

```bash
pytest -v
```

The tests use a temporary file, so your real `courses.json` is never modified. They cover every endpoint, the bonus stats endpoint and all the error cases (21 tests).

### Option B — curl script (server must be running)

Terminal 1:
```bash
python app.py
```
Terminal 2:
```bash
bash test_api.sh
```
Each line shows `PASS` or `FAIL`, the HTTP status, and the start of the response. At the end you get a summary such as `Results: 16 passed, 0 failed`.

> On Windows, run `test_api.sh` from **Git Bash** or WSL, or copy the curl commands from section 5 one by one.

### Option C — manual checks

After adding a course, open `courses.json`: you will see the course saved there. Stop and restart the server, then run `curl http://localhost:5000/api/courses` — the data is still there.

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` (with your virtual environment activated). |
| `Address already in use` / port 5000 busy | Another program uses port 5000 (on macOS, often AirPlay Receiver). Stop it, or change `port=5000` at the bottom of `app.py`, e.g. to `5001`. |
| `curl: (7) Failed to connect` | The server is not running. Start it with `python app.py` in another terminal. |
| `Request body must be a JSON object` | You forgot `-H "Content-Type: application/json"` or the JSON is malformed (check quotes and commas). |
| curl JSON fails on Windows CMD | CMD does not accept single quotes. Use double quotes and escape the inner ones: `-d "{\"status\": \"Completed\"}"`, or use Git Bash / PowerShell. |
| `Data file is corrupted` | `courses.json` was edited by hand and is not valid JSON. Fix it, or delete it (a new empty one is created automatically). |
| 404 `Endpoint not found` | Check the URL: it is `/api/courses`, not `/courses`. |

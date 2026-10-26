# GenAI prompts used for CodeCraftHub

These are the prompts entered in the AI classroom, in order. The generated code was then reviewed, corrected and tested by hand (see "Developer review" below).

## 1. Requirements gathering

```
I want to create a simple personalized learning platform called CodeCraftHub where developers can track courses they want to learn. Requirements: - Use Python with Flask framework - Store course data in a simple JSON text file (NO database needed) - No authentication or user management needed - Focus on learning REST API basics Each course should track the following: - Course name - Description - Target completion date - Current status (Not Started, In Progress, Completed) Recommend: 1. A simple project structure for beginners 2. The REST API endpoints to be created 3. How to store and retrieve data from a JSON file
```

## 2. Application code

```
Now create the complete Python Flask code for app.py with these requirements: 1. Create a Flask REST API with all CRUD operations for courses 2. Store data in a JSON file called "courses.json" 3. Include these endpoints: - POST /api/courses - Add a new course - GET /api/courses - Get all courses - GET /api/courses/<id> - Get a specific course - PUT /api/courses/<id> - Update a course - DELETE /api/courses/<id> - Delete a course 4. Each course must have: - id (auto-generated, starting from 1) - name (required) - description (required) - target_date (required, format YYYY-MM-DD) - status (required, must be: "Not Started", "In Progress", or "Completed") - created_at (auto-generated timestamp) 5. Include proper error handling for: - Missing required fields - Course not found - Invalid status values - File read/write errors 6. Add helpful comments throughout the code for beginners 7. Make sure the app creates courses.json automatically if it doesn't exist
```

## 3. Test cases

```
Create comprehensive test cases for the CodeCraftHub API. Provide: 1. curl commands to test each endpoint 2. Example JSON payloads for POST and PUT requests 3. Expected responses for successful operations 4. Test cases for error scenarios (missing fields, invalid data, course not found) Make the tests easy to copy and paste for beginners.
```

## 4. Documentation

```
Create a complete README.md file for the CodeCraftHub project that includes: 1. Project overview and description 2. Features list 3. Installation instructions (step-by-step) 4. How to run the application 5. API endpoints documentation with examples 6. Testing instructions 7. Troubleshooting common issues 8. Project structure explanation Write it for beginners who are learning REST APIs for the first time.
```

## 5. Challenge — statistics endpoint

```
Add a new endpoint GET /api/courses/stats that returns statistics about courses:
- Total number of courses
- Number of courses by status (Not Started, In Progress, Completed)
```

## Developer review — issues found in the first AI draft and fixed

| Issue in generated code | Fix applied |
|---|---|
| `target_date` was required to be `YYYY-MM-DD` but never checked | Validated with `datetime.strptime(value, "%Y-%m-%d")` (also rejects impossible dates like 2026-02-30) |
| `PUT` did not validate the new `status` | Same validation used for create and update |
| Empty strings (`"name": ""`) were accepted | Name/description must be non-empty strings |
| A request without JSON (or wrong Content-Type) crashed with a 415/500 | `request.get_json(silent=True)` + clear 400 message |
| A corrupted `courses.json` silently returned `[]`, and the next save erased all data | Corruption now returns a 500 error and the file is left untouched |
| `save_courses()` returned `False` but callers ignored it | Write errors raise `StorageError`, turned into a JSON 500 response |
| Writing the file directly could leave it half-written | Write to a temp file, then `os.replace()` (atomic) |
| `courses.json` was created in whatever folder you ran from | Path is now relative to `app.py` |
| Unknown URLs returned an HTML page | JSON error handlers for 404, 405, 500 |

---

# Part 2 — Frontend dashboard (Bolt.diy)

Single prompt used in Bolt.diy (backend is Python/Flask, so the base URL is `http://localhost:5000`):

```
Create a learning management dashboard with API operations.

Requirements:
1. Single HTML file with embedded CSS and JavaScript
2. Display all courses in a table/card layout
3. Include a form to add new courses
4. Allow editing courses inline or in a modal
5. Include delete buttons for each course
6. Use vanilla JavaScript (no frameworks like React)
7. Use basic CSS for styling (no frameworks like Bootstrap)
8. Generate only one HTML file with all JS and CSS
9. Focus on calling backend APIs
10. Do not use any database

Technical details:
- Base API URL: http://localhost:5000/api/courses
- All API calls should handle loading states and errors
- The GET /api/courses response is {"success": true, "count": N, "courses": [...]}; errors are {"success": false, "error": "message"}

API endpoints to implement:
1. GET /api/courses - fetch all courses
2. POST /api/courses - create new course (body: name, description, target_date, status)
3. PUT /api/courses/{id} - update course (body: any fields to update)
4. DELETE /api/courses/{id} - delete course

Course fields:
- id (read-only, auto-generated by backend, a number)
- name (required, text input)
- description (required, textarea)
- target_date (required, date input in YYYY-MM-DD format)
- status (required, dropdown with: "Not Started", "In Progress", "Completed")
- created_at (read-only, displayed as formatted date)

Design:
- Header with "CodeCraftHub: Your Learning Management Platform"
- Add Course form at the top with all fields
- Course list below showing all courses
- Each course should have Edit and Remove buttons
- Use a simple, clean table or card layout
- Show loading spinner while fetching/saving data
- Show success/error messages for all operations
- Make it responsive for mobile devices

Colors:
- Use a professional purple/amber theme:
	- #8B5CF6 for primary
	- #F59E0B for success
	- #EF4444 for delete

Error handling:
- Show error if API calls fail
- Validate all required fields before submission
- Show user-friendly error messages
```

The only additions to the lab's template are the response-shape line and "a number" for `id`. They prevent the two most common bugs in generated dashboards: reading the response as a plain array, and comparing a string id with a number id.

## Developer review — fixes applied to the generated frontend

| Issue | Fix |
|---|---|
| Lab example `courses.html`: Edit never opens, because `editingCourseId === course.id` compares `"1"` (string from `onclick`) with `1` (number) | Ids compared with `String(a) === String(b)` |
| Dashboard on Live Server (port 5500) calling Flask (port 5000) is blocked by the browser (CORS) | Backend adds `Access-Control-Allow-*` headers (`add_cors_headers` in `app.py`) |
| `http://localhost:5000` does not work when the lab IDE is opened through a proxy URL | `detectApiBase()` picks same-origin, localhost, or the `-5000` proxy host automatically. Flask also serves the page at `/dashboard` |
| Backend error messages were hidden behind a generic "Failed to …" | The dashboard shows the API's `error` text |
| `new Date("2026-12-31")` is parsed as UTC, so dates show one day early in the Americas | Dates are parsed as local `Y-M-D` |
| Course text was inserted with `innerHTML` in some places (XSS risk) | Every value is HTML-escaped |
| Edit / delete gave no feedback (alert only) | Toast messages, button spinners, confirm before removing |

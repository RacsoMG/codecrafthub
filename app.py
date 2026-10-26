"""
CodeCraftHub - Personalized Learning Platform for Developers
=============================================================
A simple REST API (Flask) to track the courses you want to learn.
Data is stored in a plain JSON file (courses.json) - no database needed.

Run:   python app.py
URL:   http://localhost:5000
"""

from flask import Flask, jsonify, request
from datetime import datetime
import json
import os

app = Flask(__name__)

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------

# The JSON file lives next to app.py, no matter where you launch it from.
# You can override it with an environment variable (handy for tests).
DATA_FILE = os.environ.get(
    "CODECRAFTHUB_DATA_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "courses.json"),
)

# The only status values a course may have
VALID_STATUSES = ["Not Started", "In Progress", "Completed"]

# Fields the client must send when creating a course
REQUIRED_FIELDS = ["name", "description", "target_date", "status"]


# Custom exception so file problems can be reported as a clean JSON error
class StorageError(Exception):
    pass


# ----------------------------------------------------------------------------
# HELPER FUNCTIONS (data storage)
# ----------------------------------------------------------------------------

def load_courses():
    """Read all courses from the JSON file.

    - If the file does not exist yet, create it with an empty list.
    - If the file cannot be read or is not valid JSON, raise StorageError.
    """
    if not os.path.exists(DATA_FILE):
        save_courses([])  # create the file automatically
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:          # an empty file counts as "no courses"
                return []
            courses = json.loads(content)
    except json.JSONDecodeError as e:
        raise StorageError(f"Data file is corrupted (invalid JSON): {e}")
    except OSError as e:
        raise StorageError(f"Could not read data file: {e}")

    if not isinstance(courses, list):
        raise StorageError("Data file must contain a JSON list of courses")
    return courses


def save_courses(courses):
    """Write the full list of courses to the JSON file.

    We write to a temporary file first and then rename it, so a crash in the
    middle of writing can never leave a half-written (corrupted) courses.json.
    """
    tmp_file = DATA_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(courses, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, DATA_FILE)
    except OSError as e:
        raise StorageError(f"Could not write data file: {e}")


def get_next_id(courses):
    """Return the next free ID (starts at 1)."""
    return max((c["id"] for c in courses), default=0) + 1


def find_course(courses, course_id):
    """Return (index, course) for the given ID, or (None, None) if missing."""
    for index, course in enumerate(courses):
        if course["id"] == course_id:
            return index, course
    return None, None


# ----------------------------------------------------------------------------
# HELPER FUNCTIONS (validation)
# ----------------------------------------------------------------------------

def get_json_body():
    """Return the request body as a dict, or None if it is not a JSON object."""
    data = request.get_json(silent=True)  # silent=True -> None instead of error
    return data if isinstance(data, dict) else None


def validate_fields(data, partial=False):
    """Check the course fields in `data`.

    partial=False -> creating a course: every required field must be present.
    partial=True  -> updating a course: only the fields sent are checked.
    Returns an error message (str) or None if everything is valid.
    """
    if not partial:
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            return f"Missing required field(s): {', '.join(missing)}"

    # Text fields must be non-empty strings
    for field in ("name", "description"):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                return f"'{field}' must be a non-empty string"

    # Date must be a real calendar date in YYYY-MM-DD format
    if "target_date" in data:
        value = data["target_date"]
        try:
            if not isinstance(value, str):
                raise ValueError
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return "'target_date' must be a valid date in YYYY-MM-DD format"

    # Status must be one of the allowed values
    if "status" in data and data["status"] not in VALID_STATUSES:
        return f"'status' must be one of: {', '.join(VALID_STATUSES)}"

    return None


def error(message, status_code):
    """Build a consistent JSON error response."""
    return jsonify({"success": False, "error": message}), status_code


# ----------------------------------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    """Welcome message listing the available endpoints."""
    return jsonify({
        "message": "Welcome to the CodeCraftHub API!",
        "endpoints": {
            "POST /api/courses": "Add a new course",
            "GET /api/courses": "Get all courses",
            "GET /api/courses/<id>": "Get a specific course",
            "PUT /api/courses/<id>": "Update a course",
            "DELETE /api/courses/<id>": "Delete a course",
            "GET /api/courses/stats": "Course statistics by status",
        },
    }), 200


@app.route("/api/courses", methods=["POST"])
def add_course():
    """Create a new course. All four fields are required."""
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object "
                     "(did you set 'Content-Type: application/json'?)", 400)

    problem = validate_fields(data, partial=False)
    if problem:
        return error(problem, 400)

    courses = load_courses()
    new_course = {
        "id": get_next_id(courses),
        "name": data["name"].strip(),
        "description": data["description"].strip(),
        "target_date": data["target_date"],
        "status": data["status"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    courses.append(new_course)
    save_courses(courses)

    return jsonify({
        "success": True,
        "message": "Course added successfully",
        "course": new_course,
    }), 201


@app.route("/api/courses", methods=["GET"])
def get_all_courses():
    """Return every course."""
    courses = load_courses()
    return jsonify({"success": True, "count": len(courses), "courses": courses}), 200


# NOTE: this route is defined before /<int:course_id>; because the ID route only
# accepts integers, "stats" can never be confused with a course ID anyway.
@app.route("/api/courses/stats", methods=["GET"])
def get_stats():
    """BONUS: total number of courses and how many are in each status."""
    courses = load_courses()
    by_status = {status: 0 for status in VALID_STATUSES}
    for course in courses:
        if course.get("status") in by_status:
            by_status[course["status"]] += 1

    return jsonify({
        "success": True,
        "stats": {"total_courses": len(courses), "by_status": by_status},
    }), 200


@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    """Return one course by its ID."""
    _, course = find_course(load_courses(), course_id)
    if course is None:
        return error(f"Course with id {course_id} not found", 404)
    return jsonify({"success": True, "course": course}), 200


@app.route("/api/courses/<int:course_id>", methods=["PUT"])
def update_course(course_id):
    """Update one or more fields of an existing course."""
    data = get_json_body()
    if data is None:
        return error("Request body must be a JSON object "
                     "(did you set 'Content-Type: application/json'?)", 400)

    courses = load_courses()
    index, course = find_course(courses, course_id)
    if course is None:
        return error(f"Course with id {course_id} not found", 404)

    updatable = [f for f in REQUIRED_FIELDS if f in data]
    if not updatable:
        return error(f"Provide at least one field to update: "
                     f"{', '.join(REQUIRED_FIELDS)}", 400)

    problem = validate_fields(data, partial=True)
    if problem:
        return error(problem, 400)

    # Only change the fields that were sent; id and created_at never change
    for field in updatable:
        value = data[field]
        course[field] = value.strip() if isinstance(value, str) else value
    course["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    courses[index] = course
    save_courses(courses)

    return jsonify({
        "success": True,
        "message": "Course updated successfully",
        "course": course,
    }), 200


@app.route("/api/courses/<int:course_id>", methods=["DELETE"])
def delete_course(course_id):
    """Delete a course by its ID."""
    courses = load_courses()
    index, course = find_course(courses, course_id)
    if course is None:
        return error(f"Course with id {course_id} not found", 404)

    deleted = courses.pop(index)
    save_courses(courses)

    return jsonify({
        "success": True,
        "message": "Course deleted successfully",
        "deleted_course": deleted,
    }), 200


# ----------------------------------------------------------------------------
# GLOBAL ERROR HANDLERS (always answer with JSON, never an HTML error page)
# ----------------------------------------------------------------------------

@app.errorhandler(StorageError)
def handle_storage_error(e):
    return error(str(e), 500)


@app.errorhandler(404)
def handle_not_found(e):
    return error("Endpoint not found", 404)


@app.errorhandler(405)
def handle_method_not_allowed(e):
    return error("Method not allowed for this endpoint", 405)


@app.errorhandler(500)
def handle_internal_error(e):
    return error("Internal server error", 500)


# ----------------------------------------------------------------------------
# START THE SERVER
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    load_courses()  # makes sure courses.json exists before the first request
    print("CodeCraftHub API is starting...")
    print(f"Data will be stored in: {DATA_FILE}")
    print("API will be available at: http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)

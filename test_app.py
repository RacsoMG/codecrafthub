"""
Automated tests for the CodeCraftHub API (run with:  pytest -v)

Each test uses its own temporary courses.json, so your real data is never touched.
"""

import json
import pytest

import app as codecrafthub

VALID_COURSE = {
    "name": "Python Basics",
    "description": "Learn Python fundamentals",
    "target_date": "2026-12-31",
    "status": "Not Started",
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A Flask test client that stores data in a temporary file."""
    data_file = tmp_path / "courses.json"
    monkeypatch.setattr(codecrafthub, "DATA_FILE", str(data_file))
    codecrafthub.app.config["TESTING"] = True
    with codecrafthub.app.test_client() as c:
        c.data_file = data_file
        yield c


def add(client, **overrides):
    return client.post("/api/courses", json={**VALID_COURSE, **overrides})


# ---------------------------- happy paths -----------------------------------

def test_file_created_automatically(client):
    assert not client.data_file.exists()
    r = client.get("/api/courses")
    assert r.status_code == 200
    assert r.get_json() == {"success": True, "count": 0, "courses": []}
    assert client.data_file.exists()


def test_create_course(client):
    r = add(client)
    assert r.status_code == 201
    course = r.get_json()["course"]
    assert course["id"] == 1
    assert course["name"] == "Python Basics"
    assert "created_at" in course
    # data really persisted in the JSON file
    assert json.loads(client.data_file.read_text())[0]["name"] == "Python Basics"


def test_ids_increment(client):
    assert add(client).get_json()["course"]["id"] == 1
    assert add(client, name="Flask").get_json()["course"]["id"] == 2


def test_get_all_and_one(client):
    add(client)
    add(client, name="Flask")
    r = client.get("/api/courses")
    assert r.get_json()["count"] == 2
    r = client.get("/api/courses/2")
    assert r.status_code == 200
    assert r.get_json()["course"]["name"] == "Flask"


def test_update_course(client):
    add(client)
    r = client.put("/api/courses/1", json={"status": "In Progress"})
    assert r.status_code == 200
    course = r.get_json()["course"]
    assert course["status"] == "In Progress"
    assert course["name"] == "Python Basics"      # untouched field kept
    assert "updated_at" in course


def test_delete_course(client):
    add(client)
    r = client.delete("/api/courses/1")
    assert r.status_code == 200
    assert r.get_json()["deleted_course"]["id"] == 1
    assert client.get("/api/courses/1").status_code == 404


def test_stats(client):
    add(client)
    add(client, status="In Progress")
    add(client, status="Completed")
    add(client, status="Completed")
    stats = client.get("/api/courses/stats").get_json()["stats"]
    assert stats == {
        "total_courses": 4,
        "by_status": {"Not Started": 1, "In Progress": 1, "Completed": 2},
    }


# ---------------------------- error cases -----------------------------------

def test_missing_fields(client):
    r = client.post("/api/courses", json={"name": "Incomplete"})
    assert r.status_code == 400
    assert "description" in r.get_json()["error"]


@pytest.mark.parametrize("bad", [
    {"status": "Finished"},
    {"target_date": "31-12-2026"},
    {"target_date": "2026-02-30"},
    {"name": ""},
    {"description": "   "},
])
def test_invalid_values_on_create(client, bad):
    r = add(client, **bad)
    assert r.status_code == 400
    assert r.get_json()["success"] is False


def test_invalid_status_on_update(client):
    add(client)
    r = client.put("/api/courses/1", json={"status": "Done"})
    assert r.status_code == 400


def test_empty_update(client):
    add(client)
    r = client.put("/api/courses/1", json={})
    assert r.status_code == 400


def test_not_json_body(client):
    r = client.post("/api/courses", data="hello", content_type="text/plain")
    assert r.status_code == 400


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_course_not_found(client, method):
    kwargs = {"json": {"status": "Completed"}} if method == "put" else {}
    r = getattr(client, method)("/api/courses/999", **kwargs)
    assert r.status_code == 404
    assert r.get_json() == {"success": False, "error": "Course with id 999 not found"}


def test_corrupted_file(client):
    client.data_file.write_text("{ not valid json")
    r = client.get("/api/courses")
    assert r.status_code == 500
    assert "corrupted" in r.get_json()["error"]


def test_unknown_endpoint_returns_json(client):
    r = client.get("/api/nothing-here")
    assert r.status_code == 404
    assert r.get_json()["success"] is False

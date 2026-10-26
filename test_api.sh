#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# CodeCraftHub - curl test script
# Start the server first (python app.py), then in another terminal:
#     bash test_api.sh
# Each test prints the HTTP status it got and whether it matches the expected one.
# ---------------------------------------------------------------------------

BASE_URL="${BASE_URL:-http://localhost:5000}"
PASS=0; FAIL=0

# run_test "<description>" <expected_status> <curl args...>
run_test() {
  local desc="$1" expected="$2"; shift 2
  local body status
  body=$(curl -s -w '\n%{http_code}' "$@")
  status=$(echo "$body" | tail -n1)
  body=$(echo "$body" | sed '$d')
  if [ "$status" = "$expected" ]; then
    echo "PASS [$status] $desc"; PASS=$((PASS+1))
  else
    echo "FAIL [got $status, expected $expected] $desc"; FAIL=$((FAIL+1))
  fi
  echo "     $body" | tr -d '\n' | cut -c1-200; echo
}

JSON=(-H "Content-Type: application/json")

echo "== Happy path =="
run_test "Add course 'Python Basics'" 201 -X POST "$BASE_URL/api/courses" "${JSON[@]}" \
  -d '{"name":"Python Basics","description":"Learn Python fundamentals","target_date":"2026-12-31","status":"Not Started"}'

# Remember the id the server gave us, so the script works even if courses.json already has data
ID=$(curl -s "$BASE_URL/api/courses" | python3 -c "import sys,json; print(json.load(sys.stdin)['courses'][-1]['id'])")

run_test "Add course 'Flask REST APIs'" 201 -X POST "$BASE_URL/api/courses" "${JSON[@]}" \
  -d '{"name":"Flask REST APIs","description":"Build APIs with Flask","target_date":"2027-03-15","status":"In Progress"}'
run_test "Get all courses"            200 "$BASE_URL/api/courses"
run_test "Get course $ID"             200 "$BASE_URL/api/courses/$ID"
run_test "Update course $ID status"   200 -X PUT "$BASE_URL/api/courses/$ID" "${JSON[@]}" -d '{"status":"In Progress"}'
run_test "Statistics (bonus)"         200 "$BASE_URL/api/courses/stats"

echo; echo "== Error cases =="
run_test "Missing required fields"    400 -X POST "$BASE_URL/api/courses" "${JSON[@]}" -d '{"name":"Incomplete Course"}'
run_test "Invalid status"             400 -X POST "$BASE_URL/api/courses" "${JSON[@]}" \
  -d '{"name":"Test","description":"Test","target_date":"2026-12-31","status":"Finished"}'
run_test "Invalid date format"        400 -X POST "$BASE_URL/api/courses" "${JSON[@]}" \
  -d '{"name":"Test","description":"Test","target_date":"31/12/2026","status":"Not Started"}'
run_test "Body is not JSON"           400 -X POST "$BASE_URL/api/courses" -d 'hello'
run_test "Invalid status on update"   400 -X PUT "$BASE_URL/api/courses/$ID" "${JSON[@]}" -d '{"status":"Done"}'
run_test "Get missing course"         404 "$BASE_URL/api/courses/999999"
run_test "Update missing course"      404 -X PUT "$BASE_URL/api/courses/999999" "${JSON[@]}" -d '{"status":"Completed"}'
run_test "Delete missing course"      404 -X DELETE "$BASE_URL/api/courses/999999"

echo; echo "== Cleanup =="
run_test "Delete course $ID"          200 -X DELETE "$BASE_URL/api/courses/$ID"
run_test "Course $ID is gone"         404 "$BASE_URL/api/courses/$ID"

echo; echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]

"""Simple test to check exam attempt flow."""
import requests
import json
import time

base_url = "http://localhost:8000"

# Step 1: Register user
timestamp = int(time.time())
user_data = {
    "email": f"test_{timestamp}@example.com",
    "password": "Pass123!",
    "full_name": "Test"
}
print("1. Registering user...")
resp = requests.post(f"{base_url}/auth/register", json=user_data)
print(f"   Status: {resp.status_code}")
if resp.status_code != 201:
    print(f"   Error: {resp.text}")
    exit(1)
user_id = resp.json()['user_id']
print(f"   User ID: {user_id}")

# Step 2: Create ministry question
print("\n2. Creating ministry question...")
q_data = {
    "subject": "Math",
    "grade": "12",
    "year": 2023,
    "session": "first",
    "question_text": "What is 2+2?",
    "answer_key": "4",
    "question_type": "multiple_choice",
    "difficulty_level": "easy",
    "options": [{"id": "A", "text": "3"}, {"id": "B", "text": "4"}],
    "correct_option": "B"
}
resp = requests.post(f"{base_url}/exams/ministry-questions/", json=q_data)
print(f"   Status: {resp.status_code}")
if resp.status_code != 201:
    print(f"   Error: {resp.text}")
    exit(1)
question_id = resp.json()['id']
print(f"   Question ID: {question_id}")

# Step 3: Create exam
print("\n3. Creating exam...")
exam_data = {
    "title": "Test Exam",
    "description": "Test",
    "total_time_minutes": 30,
    "passing_score": 50.0,
    "ministry_question_ids": [question_id]
}
resp = requests.post(f"{base_url}/exams/from-ministry-questions", json=exam_data)
print(f"   Status: {resp.status_code}")
if resp.status_code != 201:
    print(f"   Error: {resp.text}")
    exit(1)
exam_id = resp.json()['id']
print(f"   Exam ID: {exam_id}")

# Step 4: Start attempt
print("\n4. Starting attempt...")
try:
    resp = requests.post(
        f"{base_url}/exams/ministry/{exam_id}/start",
        params={"user_id": user_id}
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 201:
        print(f"   Error: {resp.text}")
        exit(1)
    attempt_id = resp.json()['id']
    print(f"   Attempt ID: {attempt_id}")
except Exception as e:
    print(f"   Exception: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✓ All steps completed successfully!")

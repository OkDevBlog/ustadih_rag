import requests, time, json
base_url = 'http://localhost:8000'

# Register user
user_data = {"email": f"dbg_{int(time.time())}@test.com", "password": "Pass1234", "full_name": "Dbg"}
print('Registering...')
resp = requests.post(f'{base_url}/auth/register', json=user_data)
print('register status', resp.status_code)
print(resp.text)
user_id = resp.json().get('user_id')

# Create 1 question
q = {
    "subject": "Math",
    "grade": "12",
    "year": 2023,
    "session": "first",
    "question_text": "What is 2+2?",
    "answer_key": "4",
    "question_type": "multiple_choice",
    "difficulty_level": "beginner",
    "options": [{"id":"A","text":"3"},{"id":"B","text":"4"}],
    "correct_option": "B"
}
print('Creating question...')
r = requests.post(f'{base_url}/exams/ministry-questions/', json=q)
print('question status', r.status_code)
print(r.text)
question_id = r.json().get('id')

# Create exam
exam_data = {"title":"Dbg Exam","description":"dbg","total_time_minutes":30,"passing_score":50.0,"ministry_question_ids":[question_id]}
print('Creating exam...')
re = requests.post(f'{base_url}/exams/from-ministry-questions', json=exam_data)
print('exam status', re.status_code)
print(re.text)
exam_id = re.json().get('id')

# Start attempt
print('Starting attempt...')
start = requests.post(f'{base_url}/exams/ministry/{exam_id}/start', params={"user_id": user_id})
print('start status', start.status_code)
print(start.text)


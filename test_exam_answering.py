"""Test exam answering flow for ministry questions."""
import requests
import json

base_url = "http://localhost:8000"

def test_full_exam_flow():
    """Test complete exam flow: create exam, start attempt, submit answers, view results."""
    print("\n=== Full Ministry Exam Answering Flow ===\n")
    
    # Step 1: Register a user
    print("Step 1: Registering user...")
    import time
    timestamp = int(time.time())
    user_data = {
        "email": f"student_{timestamp}@exam.com",
        "password": "StudentPass123",
        "full_name": "Test Student"
    }
    try:
        response = requests.post(f"{base_url}/auth/register", json=user_data)
        if response.status_code == 201:
            user_response = response.json()
            user_id = user_response['user_id']
            print(f"[OK] User registered: {user_id}")
        else:
            print(f"[ERROR] Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    # Step 2: Create ministry questions with multiple choice options
    print("\nStep 2: Creating ministry questions...")
    questions = [
        {
            "subject": "Math",
            "grade": "12",
            "year": 2023,
            "session": "first",
            "question_text": "What is 2 + 2?",
            "answer_key": "4",
            "question_type": "multiple_choice",
            "difficulty_level": "beginner",
            "options": [
                {"id": "A", "text": "3"},
                {"id": "B", "text": "4"},
                {"id": "C", "text": "5"},
                {"id": "D", "text": "6"}
            ],
            "correct_option": "B"
        },
        {
            "subject": "Math",
            "grade": "12",
            "year": 2023,
            "session": "first",
            "question_text": "What is the square root of 16?",
            "answer_key": "4",
            "question_type": "multiple_choice",
            "difficulty_level": "beginner",
            "options": [
                {"id": "A", "text": "2"},
                {"id": "B", "text": "3"},
                {"id": "C", "text": "4"},
                {"id": "D", "text": "5"}
            ],
            "correct_option": "C"
        },
        {
            "subject": "Math",
            "grade": "12",
            "year": 2023,
            "session": "first",
            "question_text": "What is 5 * 3?",
            "answer_key": "15",
            "question_type": "multiple_choice",
            "difficulty_level": "beginner",
            "options": [
                {"id": "A", "text": "10"},
                {"id": "B", "text": "12"},
                {"id": "C", "text": "15"},
                {"id": "D", "text": "20"}
            ],
            "correct_option": "C"
        }
    ]
    
    question_ids = []
    for q in questions:
        try:
            response = requests.post(f"{base_url}/exams/ministry-questions/", json=q)
            if response.status_code == 201:
                data = response.json()
                question_ids.append(data['id'])
                print(f"[OK] Question added: {data['id']}")
            else:
                print(f"[ERROR] Failed to add question: {response.text}")
        except Exception as e:
            print(f"[ERROR] {e}")
    
    if len(question_ids) < 3:
        print("ERROR: Not all questions were added.")
        return
    
    # Step 3: Create exam with these questions
    print("\nStep 3: Creating exam from ministry questions...")
    exam_data = {
        "title": "Math Quiz",
        "description": "Basic Math Questions",
        "total_time_minutes": 30,
        "passing_score": 70.0,
        "ministry_question_ids": question_ids
    }
    
    try:
        response = requests.post(f"{base_url}/exams/from-ministry-questions", json=exam_data)
        if response.status_code == 201:
            exam = response.json()
            exam_id = exam['id']
            print(f"[OK] Exam created: {exam_id}")
            print(f"  Questions: {exam['total_questions']}")
        else:
            print(f"[ERROR] Failed to create exam: {response.text}")
            return
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    # Step 4: Start exam attempt
    print("\nStep 4: Starting exam attempt...")
    try:
        response = requests.post(
            f"{base_url}/exams/ministry/{exam_id}/start",
            params={"exam_id": exam_id, "user_id": user_id}
        )
        if response.status_code == 201:
            attempt = response.json()
            attempt_id = attempt['id']
            print(f"[OK] Exam attempt started: {attempt_id}")
            print(f"  Started at: {attempt['started_at']}")
        else:
            print(f"[ERROR] Failed to start attempt: status={response.status_code}")
            print(f"Response: {response.text}")
            try:
                print(f"JSON: {response.json()}")
            except:
                pass
            return
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Submit answers
    print("\nStep 5: Submitting answers...")
    answers = [
        {"ministry_question_id": question_ids[0], "answer": "B"},  # Correct
        {"ministry_question_id": question_ids[1], "answer": "C"},  # Correct
        {"ministry_question_id": question_ids[2], "answer": "B"},  # Wrong (correct is C)
    ]
    
    submit_data = {
        "exam_id": exam_id,
        "user_id": user_id,
        "answers": answers
    }
    
    try:
        response = requests.post(
            f"{base_url}/exams/ministry/{exam_id}/submit",
            json=submit_data
        )
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Answers submitted")
            print(f"  Total Score: {result['total_score']}/{result['max_score']}")
            print(f"  Percentage: {(result['total_score']/result['max_score']*100):.1f}%")
            print(f"  Completed: {result['is_completed']}")
            print(f"  Submitted at: {result['submitted_at']}")
            
            # Show individual scores
            print("\n  Answer Details:")
            for qid, score in result['scores'].items():
                user_answer = result['answers'][qid]
                status = "Correct" if score == 1.0 else "Wrong"
                print(f"    Question {qid}: {user_answer} - {status}")
        else:
            print(f"[ERROR] Failed to submit answers: {response.text}")
            return
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    # Step 6: Get attempt details
    print("\nStep 6: Retrieving attempt details...")
    try:
        response = requests.get(f"{base_url}/exams/ministry/{exam_id}/attempts/{attempt_id}")
        if response.status_code == 200:
            attempt_details = response.json()
            print(f"[OK] Attempt retrieved")
            print(f"  Score: {attempt_details['total_score']}/{attempt_details['max_score']}")
            print(f"  Time Taken: {attempt_details['time_taken_seconds']} seconds")
        else:
            print(f"[ERROR] Failed to get attempt: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Step 7: Get all user attempts
    print("\nStep 7: Retrieving all user attempts for this exam...")
    try:
        response = requests.get(
            f"{base_url}/exams/ministry/{exam_id}/attempts",
            params={"user_id": user_id}
        )
        if response.status_code == 200:
            attempts = response.json()
            print(f"[OK] Found {len(attempts)} attempt(s)")
            for att in attempts:
                percentage = (att['total_score']/att['max_score']*100) if att['max_score'] > 0 else 0
                print(f"  Attempt {att['id']}: {att['total_score']}/{att['max_score']} ({percentage:.1f}%)")
        else:
            print(f"[ERROR] Failed to get attempts: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("Ministry Exam Answering - Full Flow Test")
    print("=" * 70)
    
    test_full_exam_flow()
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)

"""Test exam creation from ministry questions."""
import requests
import json

base_url = "http://localhost:8000"

def test_create_exam_from_ministry():
    """Test creating exam from ministry questions."""
    print("\n=== Test: Create Exam from Ministry Questions ===\n")
    
    # Step 1: Add ministry questions
    print("Step 1: Adding ministry questions...")
    questions = [
        {
            "subject": "Math",
            "grade": "12",
            "year": 2023,
            "session": "first",
            "question_text": "ما مشتقة الدالة f(x) = x^2 + 3x - 5؟",
            "answer_key": "f'(x) = 2x + 3",
            "question_type": "short_answer",
            "difficulty_level": "intermediate",
        },
        {
            "subject": "Math",
            "grade": "12",
            "year": 2023,
            "session": "first",
            "question_text": "احسب التكامل من 0 إلى 1 لـ x^2 dx",
            "answer_key": "1/3",
            "question_type": "short_answer",
            "difficulty_level": "advanced",
        },
        {
            "subject": "Math",
            "grade": "12",
            "year": 2023,
            "session": "first",
            "question_text": "ما هو حل المعادلة x^2 - 5x + 6 = 0؟",
            "answer_key": "x = 2 أو x = 3",
            "question_type": "short_answer",
            "difficulty_level": "beginner",
        }
    ]
    
    question_ids = []
    for q in questions:
        try:
            response = requests.post(f"{base_url}/exams/ministry-questions/", json=q)
            if response.status_code == 201:
                data = response.json()
                question_ids.append(data['id'])
                print(f"  [OK] Question added: {data['id']}")
            else:
                print(f"  [ERROR] Failed to add question: {response.text}")
        except Exception as e:
            print(f"  [ERROR] {e}")
    
    if not question_ids:
        print("ERROR: No questions were added. Cannot continue test.")
        return
    
    print(f"\nStep 2: Creating exam from {len(question_ids)} ministry questions...")
    
    # Step 2: Create exam using these questions
    exam_data = {
        "title": "Calculus Midterm Exam 2023 - Grade 12",
        "description": "Ministry examination for Grade 12 Mathematics - First Session 2023",
        "total_time_minutes": 120,
        "passing_score": 65.0,
        "instructions": "Answer all questions. Show your work for calculations.",
        "ministry_question_ids": question_ids
    }
    
    try:
        response = requests.post(f"{base_url}/exams/from-ministry-questions", json=exam_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            exam = response.json()
            exam_id = exam['id']
            print(f"[OK] Exam created successfully!")
            print(f"  Exam ID: {exam_id}")
            print(f"  Title: {exam['title']}")
            print(f"  Subject: {exam['subject']}")
            print(f"  Grade Level: {exam['grade_level']}")
            print(f"  Total Questions: {exam['total_questions']}")
            print(f"  Duration: {exam['total_time_minutes']} minutes")
            print(f"  Passing Score: {exam['passing_score']}%")
            
            # Step 3: Get exam questions
            print(f"\nStep 3: Retrieving questions linked to exam {exam_id}...")
            try:
                response = requests.get(f"{base_url}/exams/from-ministry/{exam_id}/questions")
                if response.status_code == 200:
                    linked_questions = response.json()
                    print(f"[OK] Retrieved {len(linked_questions)} questions")
                    for i, q in enumerate(linked_questions, 1):
                        print(f"  {i}. {q['subject']} - {q['question_text'][:50]}...")
                else:
                    print(f"[ERROR] Failed to get questions: {response.text}")
            except Exception as e:
                print(f"[ERROR] {e}")
        else:
            print(f"[ERROR] Failed to create exam: {response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")


def test_create_exam_with_ministry_ids():
    """Test creating exam using the main create endpoint with ministry_question_ids."""
    print("\n\n=== Test: Create Exam with ministry_question_ids parameter ===\n")
    
    # Get some questions first
    print("Step 1: Fetching some existing ministry questions...")
    try:
        response = requests.get(f"{base_url}/exams/ministry-questions/", params={"subject": "Math", "limit": 3})
        if response.status_code == 200:
            questions = response.json()
            if questions:
                question_ids = [q['id'] for q in questions[:2]]
                print(f"[OK] Found {len(questions)} questions, using {len(question_ids)} for exam")
                
                # Step 2: Create exam with these questions
                print(f"\nStep 2: Creating exam using main endpoint with {len(question_ids)} questions...")
                exam_data = {
                    "title": "Quick Math Test",
                    "subject": "Math",
                    "grade_level": "12",
                    "description": "Quick assessment",
                    "total_time_minutes": 45,
                    "passing_score": 50.0,
                    "ministry_question_ids": question_ids
                }
                
                response = requests.post(f"{base_url}/exams/", json=exam_data, params={"user_id": "test_user"})
                if response.status_code == 200:
                    exam = response.json()
                    print(f"[OK] Exam created via main endpoint!")
                    print(f"  Exam ID: {exam['id']}")
                    print(f"  Title: {exam['title']}")
                    print(f"  Total Questions: {exam['total_questions']}")
                else:
                    print(f"[ERROR] {response.text}")
            else:
                print("[ERROR] No questions found")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("Exam Creation from Ministry Questions - Testing")
    print("=" * 70)
    
    test_create_exam_from_ministry()
    test_create_exam_with_ministry_ids()
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)

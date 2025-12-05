"""Test script for Ministry Questions endpoints."""
import requests
import json

base_url = "http://localhost:8000"

def test_add_ministry_question():
    """Test adding ministry questions."""
    print("\n=== 1. Testing POST /exams/ministry-questions/ ===")
    
    # Add Math question
    math_question = {
        "subject": "Math",
        "grade": "12",
        "year": 2023,
        "session": "first",
        "question_text": "ما مشتقة الدالة f(x) = x^2 + 3x - 5؟",
        "answer_key": "f'(x) = 2x + 3",
        "question_type": "short_answer",
        "difficulty_level": "intermediate",
        "options": None,
        "correct_option": None
    }
    
    try:
        response = requests.post(f"{base_url}/exams/ministry-questions/", json=math_question)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"OK - Math question added successfully")
            print(f"  Question ID: {data['id']}")
            math_q_id = data['id']
        else:
            print(f"ERROR: {response.text}")
            return
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Add English question with multiple choice
    english_question = {
        "subject": "English",
        "grade": "12",
        "year": 2023,
        "session": "first",
        "question_text": "What is the synonym of 'eloquent'?",
        "answer_key": "Fluent, articulate, or well-spoken",
        "question_type": "multiple_choice",
        "difficulty_level": "intermediate",
        "options": [
            {"id": "A", "text": "Silent"},
            {"id": "B", "text": "Fluent"},
            {"id": "C", "text": "Rude"},
            {"id": "D", "text": "Quick"}
        ],
        "correct_option": "B"
    }
    
    try:
        response = requests.post(f"{base_url}/exams/ministry-questions/", json=english_question)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✓ English question added successfully")
            print(f"  Question ID: {data['id']}")
            english_q_id = data['id']
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Add Chemistry question - second session
    chemistry_question = {
        "subject": "Chemistry",
        "grade": "12",
        "year": 2023,
        "session": "second",
        "question_text": "ما عدد ذرات الهيدروجين في جزيء الميثان (CH4)؟",
        "answer_key": "4 ذرات هيدروجين",
        "question_type": "short_answer",
        "difficulty_level": "beginner",
        "options": None,
        "correct_option": None
    }
    
    try:
        response = requests.post(f"{base_url}/exams/ministry-questions/", json=chemistry_question)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"✓ Chemistry question added successfully")
            print(f"  Question ID: {data['id']}")
        else:
            print(f"✗ Error: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_list_ministry_questions():
    """Test retrieving ministry questions with filters."""
    print("\n=== 2. Testing GET /exams/ministry-questions/ ===")
    
    # Get all Math questions
    print("\n  a) Fetching all Math questions...")
    try:
        response = requests.get(f"{base_url}/exams/ministry-questions/", params={"subject": "Math"})
        print(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} Math questions")
            for q in data:
                print(f"    - {q['id']}: {q['question_text'][:50]}...")
        else:
            print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Get Grade 12 questions from first session
    print("\n  b) Fetching Grade 12, Session 1 questions...")
    try:
        response = requests.get(f"{base_url}/exams/ministry-questions/", 
                               params={"grade": "12", "year": 2023, "session": "first"})
        print(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} questions")
            for q in data:
                print(f"    - {q['subject']}: {q['question_text'][:40]}...")
        else:
            print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Get Chemistry questions from second session
    print("\n  c) Fetching Chemistry questions from second session...")
    try:
        response = requests.get(f"{base_url}/exams/ministry-questions/", 
                               params={"subject": "Chemistry", "session": "second"})
        print(f"  Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Found {len(data)} Chemistry questions")
            for q in data:
                print(f"    - {q['id']}: Year {q['year']}, Grade {q['grade']}")
        else:
            print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def test_get_single_question():
    """Test retrieving a single ministry question."""
    print("\n=== 3. Testing GET /exams/ministry-questions/{{question_id}} ===")
    
    # First get a question ID
    try:
        response = requests.get(f"{base_url}/exams/ministry-questions/", params={"subject": "Math"})
        if response.status_code == 200:
            data = response.json()
            if data:
                question_id = data[0]['id']
                
                # Now get that specific question
                print(f"\n  Fetching question: {question_id}")
                response = requests.get(f"{base_url}/exams/ministry-questions/{question_id}")
                print(f"  Status Code: {response.status_code}")
                if response.status_code == 200:
                    q = response.json()
                    print(f"  ✓ Question retrieved successfully")
                    print(f"    Subject: {q['subject']}")
                    print(f"    Grade: {q['grade']}, Year: {q['year']}, Session: {q['session']}")
                    print(f"    Question: {q['question_text']}")
                    print(f"    Answer Key: {q['answer_key']}")
                else:
                    print(f"  ✗ Error: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Ministry Questions Endpoints Testing")
    print("=" * 60)
    
    test_add_ministry_question()
    test_list_ministry_questions()
    test_get_single_question()
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)

import requests
import json

base_url = "http://localhost:8000"

# Test registration
register_data = {
    "email": "testuser@example.com",
    "password": "SecurePass123",
    "full_name": "Test User"
}

print("Testing /auth/register endpoint...")
try:
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response Text: {e.response.text}")

import requests
import json

base_url = "http://localhost:8000"

# First register a user
register_data = {
    "email": "logintest@example.com",
    "password": "TestPass123",
    "full_name": "Login Test User"
}

print("1. Testing /auth/register endpoint...")
try:
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 201:
        print("   Registration successful!")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

# Now test login
print("\n2. Testing /auth/login endpoint...")
login_data = {
    "email": "logintest@example.com",
    "password": "TestPass123"
}

try:
    response = requests.post(f"{base_url}/auth/login", json=login_data)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test login with wrong password
print("\n3. Testing /auth/login with wrong password...")
wrong_login = {
    "email": "logintest@example.com",
    "password": "WrongPassword"
}

try:
    response = requests.post(f"{base_url}/auth/login", json=wrong_login)
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

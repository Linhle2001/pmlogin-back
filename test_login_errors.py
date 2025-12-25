import requests
import json

base_url = "http://127.0.0.1:8000/login"

def test_login(email, password, hwid=None, description=""):
    """Test login with different scenarios"""
    data = {
        "email": email,
        "password": password
    }
    if hwid:
        data["hwid"] = hwid
    
    try:
        response = requests.post(base_url, json=data)
        result = response.json()
        print(f"\n=== {description} ===")
        print(f"Status Code: {response.status_code}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Error Code: {result.get('error_code', 'N/A')}")
        if result.get('success'):
            print(f"User ID: {result.get('data', {}).get('user', {}).get('id')}")
    except Exception as e:
        print(f"Error: {e}")

# Test cases
print("Testing Login Error Codes")
print("=" * 50)

# Test 1: Empty email
test_login("", "password", description="Empty Email")

# Test 2: Empty password  
test_login("test@example.com", "", description="Empty Password")

# Test 3: User not found
test_login("nonexistent@example.com", "password", description="User Not Found")

# Test 4: Wrong password
test_login("lelinh21102001@gmail.com", "wrongpassword", description="Wrong Password")

# Test 5: Successful login (first time - should save HWID)
test_login("lelinh21102001@gmail.com", "lelinh21102001@gmail.com", "hwid-123", description="Successful Login (First Time)")

# Test 6: Login with different HWID (should fail)
test_login("lelinh21102001@gmail.com", "lelinh21102001@gmail.com", "different-hwid", description="HWID Mismatch")

# Test 7: Login with same HWID (should succeed)
test_login("lelinh21102001@gmail.com", "lelinh21102001@gmail.com", "hwid-123", description="Successful Login (Same HWID)")
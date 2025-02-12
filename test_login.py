import requests
import json

def test_login():
    print("Testing login process...")
    
    # First request to get CSRF token
    session = requests.Session()
    initial_url = 'https://anc.apm.activecommunities.com/seattle/myaccount?onlineSiteId=0&from_original_cui=true&online=true&locale=en-US'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    
    try:
        # Get initial page
        print("Getting initial page...")
        response = session.get(initial_url, headers=headers)
        response.raise_for_status()
        
        # Try to find CSRF token
        import re
        csrf_match = re.search(r'window\.__csrfToken = "(.*?)";', response.text)
        if not csrf_match:
            print("Failed to find CSRF token")
            return False
            
        csrf_token = csrf_match.group(1)
        print(f"Found CSRF token: {csrf_token[:10]}...")
        
        # Attempt login
        login_url = 'https://anc.apm.activecommunities.com/seattle/rest/user/signin?locale=en-US'
        login_headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json;charset=utf-8',
            'Origin': 'https://anc.apm.activecommunities.com',
            'X-CSRF-Token': csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        login_data = {
            "login_name": "Seattletennisguy@gmail.com",
            "password": "ThisIsMyPassword44",
            "signin_source_app": "0",
            "from_original_cui": "true",
            "onlineSiteId": "0"
        }
        
        print("Attempting login...")
        login_response = session.post(login_url, headers=login_headers, json=login_data)
        login_response.raise_for_status()
        
        print("Login response:", login_response.json())
        return True
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    test_login()

#!/usr/bin/env python3
"""
Demo script to test the Users API with authentication and profiles.
Run this script to see the full authentication and profile management flow.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000"

async def make_request(session: aiohttp.ClientSession, method: str, endpoint: str, 
                      data: Dict[Any, Any] = None, headers: Dict[str, str] = None):
    """Make HTTP request and return response."""
    url = f"{API_BASE}{endpoint}"
    kwargs = {}
    if data:
        kwargs['json'] = data
    if headers:
        kwargs['headers'] = headers
    
    async with session.request(method, url, **kwargs) as response:
        try:
            response_data = await response.json()
        except:
            response_data = await response.text()
        
        return {
            'status': response.status,
            'data': response_data
        }

async def demo_flow():
    """Demonstrate the complete user registration, authentication, and profile management flow."""
    async with aiohttp.ClientSession() as session:
        print("🚀 Starting Users API Demo\n")
        
        # 1. Check API health
        print("1️⃣ Checking API health...")
        health = await make_request(session, 'GET', '/healthz')
        print(f"   Health check: {health['data']}")
        
        readiness = await make_request(session, 'GET', '/readyz')
        print(f"   Readiness check: {readiness['data']}\n")
        
        # 2. Register a new user
        print("2️⃣ Registering a new user...")
        user_data = {
            "email": "alice@example.com",
            "name": "Alice Johnson",
            "password": "secretpassword123"
        }
        
        register_response = await make_request(session, 'POST', '/auth/register', user_data)
        print(f"   Registration status: {register_response['status']}")
        if register_response['status'] == 201:
            print(f"   User created: {register_response['data']['email']}")
        else:
            print(f"   Registration error: {register_response['data']}")
        print()
        
        # 3. Login to get access token
        print("3️⃣ Logging in...")
        login_data = {
            "username": "alice@example.com",  # OAuth2PasswordRequestForm uses 'username'
            "password": "secretpassword123"
        }
        
        login_response = await make_request(session, 'POST', '/auth/login', login_data)
        print(f"   Login status: {login_response['status']}")
        
        if login_response['status'] != 200:
            print(f"   Login failed: {login_response['data']}")
            return
        
        access_token = login_response['data']['access_token']
        print(f"   Access token received: {access_token[:20]}...")
        
        # Set authorization header for subsequent requests
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print()
        
        # 4. Get current user info
        print("4️⃣ Getting current user info...")
        me_response = await make_request(session, 'GET', '/auth/me', headers=auth_headers)
        print(f"   Current user: {me_response['data']}\n")
        
        # 5. Get current user profile
        print("5️⃣ Getting current user profile...")
        profile_response = await make_request(session, 'GET', '/profile/me', headers=auth_headers)
        print(f"   Profile: {json.dumps(profile_response['data'], indent=2, default=str)}\n")
        
        # 6. Update profile information
        print("6️⃣ Updating profile information...")
        profile_update = {
            "bio": "I'm a software developer passionate about microservices and Kubernetes!",
            "location": "San Francisco, CA",
            "website": "https://alice-dev.com",
            "phone": "+1-555-0123"
        }
        
        update_response = await make_request(session, 'PUT', '/profile/me', 
                                           profile_update, auth_headers)
        print(f"   Profile update status: {update_response['status']}")
        print(f"   Updated profile bio: {update_response['data']['bio']}\n")
        
        # 7. Update user preferences
        print("7️⃣ Updating user preferences...")
        preferences_update = {
            "theme": "dark",
            "language": "en",
            "timezone": "America/Los_Angeles",
            "notifications_email": True,
            "notifications_sms": False,
            "privacy_public_profile": True
        }
        
        prefs_response = await make_request(session, 'PUT', '/profile/me/preferences', 
                                          preferences_update, auth_headers)
        print(f"   Preferences update status: {prefs_response['status']}")
        print(f"   Updated preferences: {json.dumps(prefs_response['data']['preferences'], indent=2)}\n")
        
        # 8. Get updated profile
        print("8️⃣ Getting final updated profile...")
        final_profile = await make_request(session, 'GET', '/profile/me', headers=auth_headers)
        print(f"   Final profile:")
        print(f"   Name: {final_profile['data']['name']}")
        print(f"   Email: {final_profile['data']['email']}")
        print(f"   Bio: {final_profile['data']['bio']}")
        print(f"   Location: {final_profile['data']['location']}")
        print(f"   Website: {final_profile['data']['website']}")
        print(f"   Theme preference: {final_profile['data']['preferences']['theme']}")
        print()
        
        # 9. Try to access admin-only endpoint (should fail)
        print("9️⃣ Testing authorization (should fail for regular user)...")
        users_list = await make_request(session, 'GET', '/users', headers=auth_headers)
        print(f"   Users list status: {users_list['status']}")
        print(f"   Expected 403 Forbidden: {users_list['data']}\n")
        
        print("✅ Demo completed successfully!")
        print("\n🔗 You can also explore the interactive API docs at:")
        print("   📖 Swagger UI: http://localhost:8000/docs")
        print("   📚 ReDoc: http://localhost:8000/redoc")

if __name__ == "__main__":
    asyncio.run(demo_flow())

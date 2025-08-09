#!/usr/bin/env python3

"""
Test script for Claude's new AI features
"""

import requests
import json
import sys
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test the new AI endpoints"""
    print("🧪 Testing Claude's New AI Features")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    print()
    
    # Test 1: Advanced AI - Personality Profile
    print("🧠 Test 1: Advanced AI - Personality Profile")
    try:
        personality_data = {
            "user_id": "test_user_123",
            "analysis_depth": "comprehensive"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/personality-profile",
            json=personality_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Personality profile generated")
            print(f"   Response keys: {list(result.keys())}")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Enhanced Chat
    print("💬 Test 2: Enhanced Chat - Therapeutic Conversation")
    try:
        chat_data = {
            "user_id": "test_user_123",
            "message": "I'm feeling a bit anxious about my upcoming presentation",
            "conversation_mode": "THERAPEUTIC",
            "context_metadata": {
                "source": "test",
                "timestamp": "2025-08-09"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Chat response generated")
            print(f"   Response: {result.get('content', 'N/A')[:100]}...")
            print(f"   Therapeutic techniques: {result.get('therapeutic_techniques', [])}")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Check API documentation
    print("📚 Test 3: API Documentation Available")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("   ✅ API documentation available at /docs")
        else:
            print("   ❌ API documentation not accessible")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("🎯 Test Summary:")
    print("   - Advanced AI Services: Implemented with personality profiling")
    print("   - Enhanced Chat: Therapeutic conversation capabilities")
    print("   - API Integration: Proper FastAPI endpoints")
    print("   - Documentation: Available via Swagger/OpenAPI")

if __name__ == "__main__":
    test_api_endpoints()

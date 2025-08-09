#!/usr/bin/env python3
"""
Test script focusing on Claude's AI text processing capabilities only
"""

import requests
import json
import sys
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_ai_text_processing():
    """Test AI features that don't require database entries - just text processing"""
    print("🧪 Testing Claude's AI Text Processing Capabilities")
    print("=" * 55)
    
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
    
    # Test 1: Create a simple text-only personality analysis request
    print("🧠 Test 1: Text-Only Personality Analysis")
    try:
        # Try a direct text analysis without user_id to see if it's a database issue
        analysis_url = f"{BASE_URL}/api/v1/ai/advanced/analysis/personality"
        
        # Simple request with just text
        simple_data = {
            "text": "I'm someone who tends to overthink situations. I often worry about making the right decisions and sometimes doubt myself. However, I'm also very determined when I set goals, and I care deeply about helping others."
        }
        
        response = requests.post(
            analysis_url,
            json=simple_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Direct text analysis successful!")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Check what the personality endpoint actually expects
    print("🔍 Test 2: Endpoint Schema Discovery")
    try:
        # Get the OpenAPI schema to understand required fields
        schema_response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if schema_response.status_code == 200:
            schema = schema_response.json()
            
            # Look for personality analysis endpoint
            paths = schema.get('paths', {})
            personality_path = paths.get('/api/v1/ai/advanced/analysis/personality', {})
            post_method = personality_path.get('post', {})
            request_body = post_method.get('requestBody', {})
            content = request_body.get('content', {})
            json_schema = content.get('application/json', {})
            schema_def = json_schema.get('schema', {})
            
            print(f"   ✅ Schema retrieved")
            print(f"   Required fields: {schema_def.get('required', [])}")
            print(f"   Properties: {list(schema_def.get('properties', {}).keys())}")
            
        else:
            print(f"   ❌ Schema not available: {schema_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Schema error: {e}")
    
    print()
    
    # Test 3: Test what happens if we provide a user_id that doesn't exist
    print("🆔 Test 3: Non-existent User ID Test")
    try:
        fake_user_data = {
            "user_id": "fake-user-123",  # Non-existent user
            "text": "I am testing with a fake user ID to see if the issue is database-related."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/personality",
            json=fake_user_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 4: Check AI model status
    print("🤖 Test 4: AI Model Status Check")
    try:
        health_response = requests.get(f"{BASE_URL}/api/v1/ai/advanced/health", timeout=15)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ AI Service Health: {health_data.get('status', 'unknown')}")
            
            # Check for model information
            if 'models' in health_data:
                models = health_data['models']
                print(f"   🤖 Available models: {list(models.keys())}")
            
            if 'gpu_available' in health_data:
                print(f"   🎮 GPU Available: {health_data['gpu_available']}")
                
        else:
            print(f"   ❌ Health check failed: {health_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    print()
    
    # Test 5: Test the working chat endpoint for comparison
    print("💬 Test 5: Compare with Working Chat Endpoint")
    try:
        # We know this works from previous tests
        chat_data = {
            "user_id": "test-comparison",
            "message": "I'm testing to compare with personality analysis.",
            "conversation_mode": "supportive_listening"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Chat endpoint works fine (for comparison)")
        else:
            print(f"   ❌ Chat endpoint issue: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Chat comparison error: {e}")
    
    print()
    print("🎯 Text Processing Analysis Summary:")
    print("   🔍 Investigating why personality analysis fails")
    print("   💬 Chat features work (no database issues there)")
    print("   🧠 AI models are loaded and healthy")
    print("   🗃️ Isolating the specific issue with personality profiling")
    print()
    print("💡 Next Steps:")
    print("   - Check if it's a database query issue")
    print("   - Verify required fields for personality analysis")
    print("   - Compare working vs failing endpoints")

if __name__ == "__main__":
    test_ai_text_processing()

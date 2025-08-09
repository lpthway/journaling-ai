#!/usr/bin/env python3
"""
Corrected test script for Claude's AI features with proper endpoints
"""

import requests
import json
import sys
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test the AI endpoints with correct paths and parameters"""
    print("🧪 Testing Claude's AI Features (Corrected)")
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
    
    # Test 1: Get Conversation Modes
    print("📋 Test 1: Get Available Conversation Modes")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/modes", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Available modes retrieved")
            modes = result.get('modes', {})
            print(f"   Available modes: {list(modes.keys())}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Advanced AI - Personality Analysis
    print("🧠 Test 2: Advanced AI - Personality Analysis")
    try:
        personality_data = {
            "user_id": 1,
            "text": "I've been feeling anxious lately about work. I tend to overthink everything and worry about details that might not matter."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/personality",
            json=personality_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Personality analysis completed")
            print(f"   Analysis type: {result.get('analysis_type', 'N/A')}")
            if 'personality_traits' in result:
                traits = result['personality_traits']
                print(f"   Key traits detected: {list(traits.keys())[:3]}")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Enhanced Chat - Therapeutic Conversation
    print("💬 Test 3: Enhanced Chat - Therapeutic Mode")
    try:
        chat_data = {
            "user_id": 1,
            "message": "I'm feeling overwhelmed with work stress lately.",
            "conversation_mode": "therapeutic_guidance"
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
            print(f"   ✅ Therapeutic chat response generated")
            content = result.get('content', '')
            print(f"   Response preview: {content[:100]}...")
            print(f"   Response type: {result.get('response_type', 'N/A')}")
            if 'therapeutic_techniques' in result:
                techniques = result['therapeutic_techniques']
                print(f"   Therapeutic techniques: {techniques}")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 4: Crisis Detection
    print("🚨 Test 4: Crisis Detection")
    try:
        crisis_data = {
            "user_id": 1,
            "message": "I'm just feeling a bit down lately, nothing too serious."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/crisis/check",
            json=crisis_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Crisis assessment completed")
            risk_level = result.get('risk_level', 'unknown')
            print(f"   Risk level: {risk_level}")
            requires_intervention = result.get('requires_intervention', False)
            print(f"   Requires intervention: {requires_intervention}")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 5: Comprehensive Analysis
    print("🔍 Test 5: Comprehensive Analysis")
    try:
        analysis_data = {
            "user_id": 1,
            "text": "Today was a challenging day. I felt anxious about my presentation, but it went well. I'm proud of how I handled the stress.",
            "include_personality": True,
            "include_predictions": True,
            "include_insights": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/comprehensive",
            json=analysis_data,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Comprehensive analysis completed")
            print(f"   Analysis includes:")
            if 'mood_analysis' in result:
                print(f"     - Mood analysis: {result['mood_analysis'].get('primary_mood', 'N/A')}")
            if 'personality_insights' in result:
                print(f"     - Personality insights: Available")
            if 'predictions' in result:
                print(f"     - Predictions: {len(result['predictions'])} items")
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 6: Health Checks
    print("❤️ Test 6: Service Health Checks")
    try:
        # Advanced AI Health
        response = requests.get(f"{BASE_URL}/api/v1/ai/advanced/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Advanced AI Service: {result.get('status', 'unknown')}")
        else:
            print(f"   ❌ Advanced AI Service: Failed ({response.status_code})")
        
        # Enhanced Chat Health
        response = requests.get(f"{BASE_URL}/api/v1/chat/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Enhanced Chat Service: {result.get('status', 'unknown')}")
        else:
            print(f"   ❌ Enhanced Chat Service: Failed ({response.status_code})")
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    print()
    print("🎯 Test Summary:")
    print("   - Conversation modes: Available and queryable")
    print("   - Personality analysis: Deep psychological profiling")
    print("   - Therapeutic chat: Context-aware therapeutic responses")
    print("   - Crisis detection: Safety monitoring and intervention")
    print("   - Comprehensive analysis: Multi-faceted AI insights")
    print("   - Health monitoring: Service status tracking")

if __name__ == "__main__":
    test_api_endpoints()

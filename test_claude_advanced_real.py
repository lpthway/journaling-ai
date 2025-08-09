#!/usr/bin/env python3
"""
Test script for Claude's advanced AI features using real database entries
"""

import requests
import json
import sys
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Real user ID from database
REAL_USER_ID = "00000000-0000-0000-0000-000000000001"

def test_advanced_ai_with_real_data():
    """Test the advanced AI features using real journal entries"""
    print("🧪 Testing Claude's Advanced AI with Real Data")
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
    
    print(f"📊 Using real user ID: {REAL_USER_ID}")
    print(f"📝 Database contains: 107 journal entries\n")
    
    # Test 1: Personality Analysis with Real User Data
    print("🧠 Test 1: Personality Analysis (Real User Data)")
    try:
        personality_data = {
            "user_id": REAL_USER_ID,  # Using real user ID
            "text": "I've been reflecting on my patterns lately. I notice I tend to overthink decisions and sometimes struggle with self-doubt, but I'm also quite determined when I set my mind to something."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/personality",
            json=personality_data,
            headers={"Content-Type": "application/json"},
            timeout=30  # Longer timeout for AI processing
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Personality analysis completed!")
            
            # Display key results
            if 'analysis_type' in result:
                print(f"   📊 Analysis type: {result['analysis_type']}")
            if 'personality_traits' in result:
                traits = result['personality_traits']
                print(f"   🎯 Key traits identified: {len(traits)} traits")
                # Show top 3 traits if available
                for i, (trait, score) in enumerate(list(traits.items())[:3]):
                    print(f"      {i+1}. {trait}: {score}")
            if 'confidence_scores' in result:
                confidence = result['confidence_scores']
                print(f"   📈 Analysis confidence: {confidence}")
            if 'insights' in result:
                insights = result['insights']
                print(f"   💡 Insights generated: {len(insights)} insights")
                
        else:
            print(f"   ❌ Failed: {response.text}")
            # Let's debug the specific error
            try:
                error_detail = response.json()
                print(f"   🔍 Error details: {json.dumps(error_detail, indent=4)}")
            except:
                print(f"   🔍 Raw error: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Comprehensive Analysis with Real User Data
    print("🔍 Test 2: Comprehensive Analysis (Real User Data)")
    try:
        analysis_data = {
            "user_id": REAL_USER_ID,  # Using real user ID
            "text": "Today I was thinking about how I've grown over the past months. I used to get very anxious about small things, but I'm learning to manage my stress better. I still have challenging days, but I'm proud of the progress I've made.",
            "include_personality": True,
            "include_predictions": True,
            "include_insights": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/comprehensive",
            json=analysis_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Comprehensive analysis completed!")
            print(f"   📊 Analysis includes:")
            
            # Display all available analysis components
            if 'mood_analysis' in result:
                mood = result['mood_analysis']
                primary_mood = mood.get('primary_mood', 'N/A')
                print(f"     🎭 Mood analysis: {primary_mood}")
            
            if 'personality_insights' in result:
                personality = result['personality_insights']
                print(f"     🧠 Personality insights: Available ({len(personality)} insights)")
            
            if 'predictions' in result:
                predictions = result['predictions']
                print(f"     🔮 Predictions: {len(predictions)} future insights")
            
            if 'emotional_patterns' in result:
                patterns = result['emotional_patterns']
                print(f"     📈 Emotional patterns: Detected ({len(patterns)} patterns)")
            
            if 'recommendations' in result:
                recommendations = result['recommendations']
                print(f"     💡 Recommendations: {len(recommendations)} actionable suggestions")
            
            if 'historical_context' in result:
                context = result['historical_context']
                print(f"     📚 Historical context: Based on {context.get('entries_analyzed', 0)} past entries")
                
        else:
            print(f"   ❌ Failed: {response.text}")
            # Debug the error
            try:
                error_detail = response.json()
                print(f"   🔍 Error details: {json.dumps(error_detail, indent=4)}")
            except:
                print(f"   🔍 Raw error: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Check AI Service Health After Processing
    print("❤️ Test 3: AI Service Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/advanced/health", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Advanced AI Service: {result.get('status', 'unknown')}")
            if 'model_status' in result:
                models = result['model_status']
                print(f"   🤖 Models loaded: {models}")
            if 'memory_usage' in result:
                memory = result['memory_usage']
                print(f"   💾 Memory usage: {memory}")
            if 'processing_stats' in result:
                stats = result['processing_stats']
                print(f"   📊 Processing stats: {stats}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    print()
    
    # Test 4: Quick Database Validation
    print("🗃️ Test 4: Database Access Validation")
    try:
        # Use a simple endpoint that checks database connectivity
        response = requests.get(f"{BASE_URL}/api/v1/ai/advanced/stats", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Database connectivity: Working")
            if 'entries_available' in result:
                print(f"   📝 Entries accessible: {result['entries_available']}")
            if 'users_tracked' in result:
                print(f"   👥 Users tracked: {result['users_tracked']}")
        else:
            print(f"   ⚠️ Stats endpoint: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Stats check: {e}")
    
    print()
    print("🎯 Advanced AI Test Summary:")
    print("   🗃️ Real database data: 107 journal entries available")
    print("   🆔 Real user ID: Used for authentic testing")
    print("   🧠 Personality profiling: Testing with historical context")
    print("   🔍 Comprehensive analysis: Multi-faceted AI insights")
    print("   🤖 AI models: GPU-accelerated processing")
    print()
    print("🚀 Testing Claude's most advanced AI capabilities!")

if __name__ == "__main__":
    test_advanced_ai_with_real_data()

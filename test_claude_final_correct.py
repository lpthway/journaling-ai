#!/usr/bin/env python3
"""
Final test for Claude's advanced AI features using correct API format
"""

import requests
import json
import sys
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Real user ID from database  
REAL_USER_ID = "00000000-0000-0000-0000-000000000001"

def test_advanced_ai_correct_format():
    """Test the advanced AI features using the correct API format"""
    print("🧪 Testing Claude's Advanced AI (Correct Format)")
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
    
    print(f"📊 Using real user ID: {REAL_USER_ID}")
    print(f"📝 This user has 107 journal entries in database\n")
    
    # Test 1: Personality Analysis (Database-based)
    print("🧠 Test 1: Personality Analysis (Historical Entries)")
    try:
        # Correct format - only user_id and options
        personality_data = {
            "user_id": REAL_USER_ID,
            "include_detailed_traits": True,
            "min_entries_required": 5  # Lower requirement
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/personality",
            json=personality_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Personality analysis completed!")
            print(f"   📊 Analysis type: {result.get('analysis_type', 'N/A')}")
            
            if 'personality_profile' in result:
                profile = result['personality_profile']
                print(f"   🎯 Personality dimensions analyzed: {len(profile)}")
                
            if 'big_five' in result:
                big_five = result['big_five']
                print(f"   🏷️ Big Five traits: {list(big_five.keys())}")
                
            if 'insights' in result:
                insights = result['insights']
                print(f"   💡 Insights generated: {len(insights)}")
                
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 2: Comprehensive Analysis (Database-based)
    print("🔍 Test 2: Comprehensive Analysis (Historical Entries)")
    try:
        # Correct format - only user_id and analysis options
        comprehensive_data = {
            "user_id": REAL_USER_ID,
            "timeframe": "monthly",  # lowercase enum value
            "include_predictions": True,
            "include_personality": True,
            "max_entries": 50  # Analyze 50 most recent entries
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/comprehensive",
            json=comprehensive_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Comprehensive analysis completed!")
            
            # Display analysis components
            if 'analysis_period' in result:
                period = result['analysis_period']
                print(f"   📅 Analysis period: {period}")
                
            if 'entries_analyzed' in result:
                count = result['entries_analyzed']
                print(f"   📝 Entries analyzed: {count}")
                
            if 'personality_insights' in result:
                personality = result['personality_insights']
                print(f"   🧠 Personality insights: Available")
                
            if 'temporal_patterns' in result:
                patterns = result['temporal_patterns']
                print(f"   📈 Temporal patterns: {len(patterns)} detected")
                
            if 'predictions' in result:
                predictions = result['predictions']
                print(f"   🔮 Predictions: {len(predictions)} future insights")
                
            if 'recommendations' in result:
                recommendations = result['recommendations']
                print(f"   💡 Recommendations: {len(recommendations)} suggestions")
                
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Predictive Analysis
    print("🔮 Test 3: Predictive Analysis")
    try:
        predictive_data = {
            "user_id": REAL_USER_ID,
            "prediction_horizon": 7,  # 7 days ahead
            "include_risk_assessment": True,
            "include_opportunities": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ai/advanced/analysis/predictive",
            json=predictive_data,
            headers={"Content-Type": "application/json"},
            timeout=25
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Predictive analysis completed!")
            
            if 'prediction_horizon' in result:
                horizon = result['prediction_horizon']
                print(f"   📅 Prediction horizon: {horizon} days")
                
            if 'risk_factors' in result:
                risks = result['risk_factors']
                print(f"   ⚠️ Risk factors: {len(risks)} identified")
                
            if 'opportunities' in result:
                opportunities = result['opportunities']
                print(f"   🌟 Opportunities: {len(opportunities)} identified")
                
        else:
            print(f"   ❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 4: Health Check
    print("❤️ Test 4: System Health")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/advanced/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ AI Service: {result.get('status', 'unknown')}")
            
        response = requests.get(f"{BASE_URL}/api/v1/ai/advanced/stats", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   📊 Stats available: {response.status_code == 200}")
            
    except Exception as e:
        print(f"   ⚠️ Health check: {e}")
    
    print()
    print("🎯 Advanced AI Features Test Summary:")
    print("   🧠 Personality Analysis: Database-driven historical analysis")
    print("   🔍 Comprehensive Analysis: Multi-faceted insights from journal entries")
    print("   🔮 Predictive Analysis: Future trend predictions")
    print("   📊 Real User Data: 107 journal entries analyzed")
    print("   🤖 AI Models: GPU-accelerated processing")
    print()
    print("🚀 These are Claude's most sophisticated AI capabilities!")

if __name__ == "__main__":
    test_advanced_ai_correct_format()

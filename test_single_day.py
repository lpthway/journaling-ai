#!/usr/bin/env python3
"""
Test single day data population to verify all fixes work
"""

import asyncio
from datetime import datetime, timedelta
from populate_data import DataPopulator

async def test_single_day():
    """Test creation of data for just one day"""
    
    populator = DataPopulator()
    
    print("🧪 Testing Single Day Data Population")
    print("=" * 50)
    
    # Create just core topics (no seasonal ones)
    print("📚 Creating core topics...")
    for topic in populator.core_topics[:2]:  # Just first 2 topics for testing
        topic_id = await populator.create_topic(topic)
        if topic_id:
            populator.created_topic_ids[topic['name']] = topic_id
        await asyncio.sleep(0.5)
    
    print(f"\n✅ Created {len(populator.created_topic_ids)} topics")
    
    # Create 1 journal entry for today
    today = datetime.now()
    print(f"\n📝 Creating journal entry for {today.strftime('%Y-%m-%d')}")
    
    theme_data = populator.select_theme_for_date(today, "en")  # English preference
    print(f"   Theme: {theme_data['theme']}")
    
    entry_data = await populator.generate_journal_entry(theme_data, today)
    topic_id = populator.get_topic_for_theme(theme_data)
    
    # Use the realistic workflow simulation
    workflow_result = await populator.simulate_real_user_workflow(entry_data, today)
    if workflow_result and workflow_result.get('workflow_complete'):
        print(f"✅ Journal entry workflow completed successfully")
    else:
        print(f"❌ Journal entry workflow had issues")
    
    # Create 1 chat session
    print(f"\n💬 Creating chat session for {today.strftime('%Y-%m-%d')}")
    
    from populate_data import SessionType
    chat_theme = [t for t in populator.chat_themes if t['language'] == 'en'][0]
    session_type = SessionType.REFLECTION_BUDDY
    
    print(f"   Theme: {chat_theme['theme']}")
    print(f"   Session Type: {session_type.value}")
    
    messages = await populator.generate_chat_conversation(chat_theme, session_type, today)
    chat_result = await populator.simulate_chat_user_workflow(session_type, chat_theme, messages, today)
    
    if chat_result and chat_result.get('workflow_complete'):
        print(f"✅ Chat session workflow completed successfully")
    else:
        print(f"❌ Chat session workflow had issues")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 SINGLE DAY TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Topics Created: {populator.stats['topics_created']}")
    print(f"✅ Journal Entries: {populator.stats['journal_entries_created']}")  
    print(f"✅ Chat Sessions: {populator.stats['chat_sessions_created']}")
    
    total_success = (populator.stats['topics_created'] + 
                    populator.stats['journal_entries_created'] + 
                    populator.stats['chat_sessions_created'])
    total_failed = (populator.stats['topics_failed'] + 
                   populator.stats['journal_entries_failed'] + 
                   populator.stats['chat_sessions_failed'])
    
    if total_failed > 0:
        print(f"❌ Failed Items: {total_failed}")
        success_rate = (total_success / (total_success + total_failed)) * 100 if total_success + total_failed > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
    else:
        print(f"🎉 All items created successfully!")
    
    print("\n🚀 Ready for full year population!")

if __name__ == "__main__":
    asyncio.run(test_single_day())
#!/bin/bash

echo "🔧 Applying Enhanced Insights Fixes"
echo "==================================="

# Backup existing files
echo "📦 Creating backups..."
cp backend/app/services/enhanced_insights_service.py backend/app/services/enhanced_insights_service.py.backup
cp backend/app/api/insights.py backend/app/api/insights.py.backup
cp frontend/src/components/Insights/AskQuestion.jsx frontend/src/components/Insights/AskQuestion.jsx.backup

# Add the new method to enhanced_insights_service.py
echo "1. Adding get_detailed_sources method..."

cat >> backend/app/services/enhanced_insights_service.py << 'EOF'

    async def get_detailed_sources(self, question: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed source information for the insights response"""
        try:
            # Get relevant content
            relevant_journal = await vector_service.search_entries(question, limit=10)
            relevant_chat = await self.search_chat_content(question, limit=10)
            
            detailed_sources = {
                'journal_entries': [],
                'conversations': []
            }
            
            # Process journal entries
            for entry in relevant_journal:
                metadata = entry.get('metadata', {})
                detailed_sources['journal_entries'].append({
                    'id': entry['id'],
                    'date': metadata.get('created_at', 'Unknown'),
                    'title': metadata.get('title', 'Untitled'),
                    'snippet': entry['content'][:150] + '...' if len(entry['content']) > 150 else entry['content'],
                    'similarity': round((1 - entry.get('distance', 0)) * 100),
                    'type': 'journal',
                    'link': f"/journal/{entry['id']}"
                })
            
            # Process chat conversations
            for chat in relevant_chat:
                detailed_sources['conversations'].append({
                    'id': chat['session_id'],
                    'date': chat['created_at'],
                    'session_type': chat['session_type'].replace('_', ' ').title(),
                    'snippet': chat['content'],
                    'similarity': round(chat['relevance_score'] * 100),
                    'message_count': chat['message_count'],
                    'type': 'conversation',
                    'link': f"/chat/{chat['session_id']}"
                })
            
            total_sources = len(detailed_sources['journal_entries']) + len(detailed_sources['conversations'])
            
            return {
                'total_sources': total_sources,
                'journal_count': len(detailed_sources['journal_entries']),
                'conversation_count': len(detailed_sources['conversations']),
                'detailed_sources': detailed_sources
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed sources: {e}")
            return {
                'total_sources': 0,
                'journal_count': 0,
                'conversation_count': 0,
                'detailed_sources': {'journal_entries': [], 'conversations': []}
            }
EOF

# Update the insights API route
echo "2. Updating insights API route..."

# Create a sed command to update the ask_question function
python3 << 'EOF'
import re

# Read the file
with open('backend/app/api/insights.py', 'r') as f:
    content = f.read()

# Find and replace the ask_question function
pattern = r'@router\.post\("/ask"\)\nasync def ask_question\(question: str\):[^@]*?(?=@|\Z)'

new_function = '''@router.post("/ask")
async def ask_question(question: str):
    """Ask a question about your journal entries AND chat conversations"""
    try:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Use enhanced insights service that includes both journals and chats
        result = await enhanced_insights_service.analyze_all_content(question, days=30)
        
        # Get detailed source information
        sources_detail = await enhanced_insights_service.get_detailed_sources(question, days=30)
        
        return {
            'question': question,
            'answer': result['answer'],
            'sources': result['sources'],
            'content_breakdown': result['content_breakdown'],
            'time_period': result['time_period'],
            'sources_used': sources_detail['total_sources'],
            'detailed_sources': sources_detail['detailed_sources']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process your question")

'''

# Replace the function
updated_content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Write back to file
with open('backend/app/api/insights.py', 'w') as f:
    f.write(updated_content)

print("✅ Updated insights.py")
EOF

echo "3. Updating frontend component..."
# Frontend update would be manual or use a more complex script

echo ""
echo "✅ Backend fixes applied!"
echo ""
echo "🔄 Now restart your backend:"
echo "   ./start-backend-only.sh"
echo ""
echo "📝 Manual step needed:"
echo "   Update frontend/src/components/Insights/AskQuestion.jsx"
echo "   with the enhanced version that shows sources with links"
echo ""
echo "🎯 Expected improvements:"
echo "   ✅ Analysis includes both journal + chat"
echo "   ✅ Shows detailed sources at the end" 
echo "   ✅ Clickable links to conversations"
echo "   ✅ Better source breakdown display"
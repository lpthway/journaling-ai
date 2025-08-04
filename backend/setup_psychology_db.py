#!/usr/bin/env python3
"""
Psychology Knowledge Database Setup Script

This script initializes and manages the psychology knowledge database.

Usage:
    python setup_psychology_db.py --action=load          # Load all psychology knowledge
    python setup_psychology_db.py --action=stats         # Show database statistics  
    python setup_psychology_db.py --action=test          # Test knowledge retrieval
    python setup_psychology_db.py --action=reset         # Reset and reload database
"""

import asyncio
import argparse
import sys
from pathlib import Path
import logging

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.psychology_knowledge_service import psychology_knowledge_service, PsychologyDomain
from app.services.psychology_data_loader import PsychologyDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PsychologyDatabaseManager:
    """Manager for psychology knowledge database operations"""
    
    def __init__(self):
        self.service = psychology_knowledge_service
        self.loader = PsychologyDataLoader()
    
    async def load_knowledge(self):
        """Load all psychology knowledge into the database"""
        print("🧠 Psychology Knowledge Database Setup")
        print("=" * 50)
        print()
        
        try:
            print("📚 Loading evidence-based psychology knowledge...")
            print("   • Cognitive Behavioral Therapy (CBT)")
            print("   • Gaming Psychology & Digital Wellness")
            print("   • Addiction Recovery Strategies")
            print("   • Mindfulness & Meditation Practices")
            print("   • Crisis Intervention Protocols")
            print("   • Emotional Regulation Techniques")
            print("   • Stress Management Methods")
            print("   • Habit Formation Science")
            print()
            
            # Load all knowledge
            count = await self.loader.load_all_psychology_knowledge()
            
            print(f"✅ Successfully loaded {count} psychology knowledge entries!")
            print()
            
            # Show statistics
            await self.show_stats()
            
        except Exception as e:
            print(f"❌ Error loading psychology knowledge: {e}")
            logger.error(f"Failed to load psychology knowledge: {e}")
    
    async def show_stats(self):
        """Display database statistics"""
        try:
            stats = await self.service.get_collection_stats()
            
            print("📊 Psychology Knowledge Database Statistics")
            print("-" * 45)
            print(f"Total Entries: {stats.get('total_entries', 0)}")
            print(f"Database Path: {stats.get('database_path', 'Unknown')}")
            print()
            
            print("Domain Breakdown:")
            domain_counts = stats.get('domain_breakdown', {})
            for domain, count in domain_counts.items():
                domain_name = domain.replace('_', ' ').title()
                print(f"  • {domain_name}: {count} entries")
            
            print()
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            logger.error(f"Failed to get statistics: {e}")
    
    async def test_retrieval(self):
        """Test knowledge retrieval functionality"""
        print("🔍 Testing Psychology Knowledge Retrieval")
        print("-" * 40)
        print()
        
        test_queries = [
            ("I'm feeling anxious about work", "Testing anxiety-related knowledge"),
            ("struggling with gaming addiction", "Testing gaming psychology knowledge"),
            ("how to build better habits", "Testing habit formation knowledge"),
            ("feeling overwhelmed and stressed", "Testing stress management knowledge"),
            ("having trouble with emotions", "Testing emotional regulation knowledge")
        ]
        
        try:
            for query, description in test_queries:
                print(f"🔎 {description}")
                print(f"   Query: '{query}'")
                
                results = await self.service.search_knowledge(
                    query=query,
                    limit=2,
                    min_credibility=0.7
                )
                
                if results:
                    print(f"   ✅ Found {len(results)} relevant sources:")
                    for i, result in enumerate(results, 1):
                        source = result['source']
                        print(f"      {i}. {source['title']} ({source['year']}) - {result['similarity']}% match")
                        print(f"         Evidence: {source['evidence_level']} | Domain: {result['domain'].replace('_', ' ').title()}")
                else:
                    print("   ❌ No relevant sources found")
                
                print()
            
            print("✅ Knowledge retrieval test completed!")
            
        except Exception as e:
            print(f"❌ Error testing retrieval: {e}")
            logger.error(f"Failed to test retrieval: {e}")
    
    async def reset_database(self):
        """Reset and reload the psychology database"""
        print("🔄 Resetting Psychology Knowledge Database")
        print("-" * 45)
        print()
        
        try:
            # Note: ChromaDB doesn't have a simple "clear all" method
            # So we'll just reload - ChromaDB will handle duplicates
            print("⚠️  Reloading psychology knowledge...")
            print("   (ChromaDB will handle any duplicates automatically)")
            print()
            
            await self.load_knowledge()
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            logger.error(f"Failed to reset database: {e}")
    
    async def interactive_search(self):
        """Interactive search interface"""
        print("🔍 Interactive Psychology Knowledge Search")
        print("-" * 42)
        print("Enter search queries to test the knowledge base.")
        print("Type 'quit' to exit.")
        print()
        
        try:
            while True:
                query = input("Search query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                print(f"\n🔎 Searching for: '{query}'")
                
                results = await self.service.search_knowledge(
                    query=query,
                    limit=3,
                    min_credibility=0.6
                )
                
                if results:
                    print(f"✅ Found {len(results)} relevant sources:\n")
                    
                    for i, result in enumerate(results, 1):
                        source = result['source']
                        print(f"{i}. {source['title']} ({source['year']})")
                        print(f"   Authors: {', '.join(source['authors'])}")
                        print(f"   Evidence Level: {source['evidence_level'].title()}")
                        print(f"   Domain: {result['domain'].replace('_', ' ').title()}")
                        print(f"   Relevance: {result['similarity']}%")
                        print(f"   Techniques: {', '.join(result['techniques'][:3])}")
                        print(f"   Content: {result['content'][:200]}...")
                        print()
                else:
                    print("❌ No relevant sources found")
                
                print("-" * 50)
                
        except KeyboardInterrupt:
            print("\n👋 Search session ended.")
        except Exception as e:
            print(f"❌ Error in interactive search: {e}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Psychology Knowledge Database Manager")
    parser.add_argument(
        '--action',
        choices=['load', 'stats', 'test', 'reset', 'search'],
        default='load',
        help='Action to perform (default: load)'
    )
    
    args = parser.parse_args()
    manager = PsychologyDatabaseManager()
    
    try:
        if args.action == 'load':
            await manager.load_knowledge()
        elif args.action == 'stats':
            await manager.show_stats()
        elif args.action == 'test':
            await manager.test_retrieval()
        elif args.action == 'reset':
            await manager.reset_database()
        elif args.action == 'search':
            await manager.interactive_search()
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
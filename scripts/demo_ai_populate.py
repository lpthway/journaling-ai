#!/usr/bin/env python3
"""
Demo script for AI-Powered Population

This demonstrates the AI-powered populate script with a small sample to test Ollama integration.
"""

import asyncio
import sys
from pathlib import Path

# Import the main populator
sys.path.append(str(Path(__file__).parent))
from populate_data import DataPopulator

async def demo():
    """Run a small demo of the AI-powered population"""
    
    print("🎯 AI-Powered Population Demo")
    print("===============================")
    print()
    print("This will create:")
    print("• 3 topics (English & German)")
    print("• 3 AI-generated journal entries") 
    print("• 2 AI-generated chat conversations")
    print()
    print("⚠️  Requires Ollama with llama3.1 model")
    print("⚠️  This will take 2-3 minutes to generate content")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Demo cancelled.")
        return
    
    populator = DataPopulator()
    await populator.populate_data(num_journal_entries=3, num_chat_sessions=2)

if __name__ == "__main__":
    asyncio.run(demo())

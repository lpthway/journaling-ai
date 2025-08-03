# Data Population Script

This script uses Ollama to generate realistic journal entries and chat conversations to populate your Journaling AI application with test data.

## Prerequisites

1. **Ollama installed and running** with the `llama3.1` model
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the model
   ollama pull llama3.1
   
   # Start Ollama (usually runs automatically)
   ollama serve
   ```

2. **Backend API running** on `http://localhost:8000`
   ```bash
   cd backend
   python run.py
   ```

3. **Python dependencies**
   ```bash
   cd scripts
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage
Generate default amounts of data (15 journal entries, 8 chat sessions):
```bash
python populate_data.py
```

### Custom Amounts
Specify how much data to generate:
```bash
# Generate 20 journal entries and 10 chat sessions
python populate_data.py --journal-entries 20 --chat-sessions 10

# Just journal entries
python populate_data.py --journal-entries 25 --chat-sessions 0

# Just chat sessions  
python populate_data.py --journal-entries 0 --chat-sessions 15
```

## What It Creates

### Journal Entries
- **Realistic content**: Personal reflections on various life themes
- **Variety of topics**: Work, relationships, health, creativity, travel, etc.
- **Natural language**: Written in first person with authentic emotions
- **Auto-tagging**: Leverages your app's automatic tagging system
- **Date distribution**: Spread across the last 30 days

### Chat Sessions
- **Different session types**: Reflection Buddy, Inner Voice, Growth Challenge, etc.
- **Natural conversations**: Multi-turn dialogues between user and AI
- **Variety of themes**: Personal growth, relationships, decision-making, etc.
- **Realistic flow**: Questions, responses, and follow-ups
- **Auto-tagging**: Tags generated based on conversation content

## Themes Used

### Journal Entry Themes
- Work stress and productivity
- Personal relationships and family
- Health and wellness journey
- Creative projects and hobbies
- Travel experiences and adventures
- Learning and personal growth
- Financial planning and goals
- Daily routines and habits
- Emotional challenges and breakthroughs
- Career development and aspirations

### Chat Session Themes
- Exploring feelings about work-life balance
- Discussing relationship challenges
- Reflecting on personal goals and motivation
- Processing anxiety and stress management
- Exploring creativity and passion projects
- Working through decision-making challenges
- Discussing self-improvement strategies
- Reflecting on past experiences and lessons learned
- Exploring future aspirations and dreams
- Processing daily emotions and thoughts

## Expected Output

The script will show real-time progress:
```
🚀 Starting data population...
📝 Generating 15 journal entries
💬 Generating 8 chat sessions

📝 Creating journal entries...
   Generating entry 1/15: work stress and productivity
✅ Created journal entry: 'Overwhelmed at Work'
   Auto-generated tags: ['stress', 'work', 'productivity', 'deadlines']
   Generating entry 2/15: personal relationships and family
✅ Created journal entry: 'Family Time Reflection'
   Auto-generated tags: ['family', 'relationships', 'gratitude', 'connection']
...

💬 Creating chat sessions...
   Generating session 1/8: exploring feelings about work-life balance (reflection_buddy)
✅ Created chat session: 'Chat about exploring feelings about work-life balance'
   Auto-generated tags: ['work-life-balance', 'reflection', 'stress', 'priorities']
...

✨ Data population complete!
```

## Testing the Results

After running the script, you can:

1. **View the data** in your frontend application
2. **Check the analytics** - mood trends, patterns, insights
3. **Test auto-tagging** - see how well the AI categorized content
4. **Explore coaching suggestions** - based on the generated content
5. **Try the chat feature** - ask questions about the "experiences"

## Troubleshooting

### "Connection refused" errors
- Make sure the backend is running on `http://localhost:8000`
- Check that the API endpoints are accessible

### Ollama errors
- Ensure Ollama is running: `ollama list` should show `llama3.1`
- If the model isn't available: `ollama pull llama3.1`
- Check Ollama is on the expected port: `http://localhost:11434`

### Import errors
- Make sure you're running from the `scripts` directory
- Install requirements: `pip install -r requirements.txt`

### Slow generation
- The script includes delays to avoid overwhelming the API
- Journal entries take ~5-10 seconds each to generate
- Chat sessions take ~15-20 seconds each (multiple AI calls)
- For faster testing, reduce the numbers: `--journal-entries 5 --chat-sessions 2`

## Customization

You can modify the script to:
- Add new themes to `journal_themes` or `chat_themes` arrays
- Change the Ollama model (update the `model="llama3.1"` lines)
- Adjust the date range for entries (change `random.randint(1, 30)`)
- Modify the conversation length (change `random.randint(3, 5)`)
- Change API endpoints if running on different ports

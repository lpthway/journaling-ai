# Data Population Scripts

These scripts use Ollama to generate realistic journal entries and chat conversations to populate your Journaling AI application with test data. **Enhanced with multilingual support (English/German) and topic functionality!**

## 🚀 Quick Start Options

### 1. **Quick Populate** (Recommended for testing)
Fast, predefined content - no Ollama required:
```bash
python quick_populate.py
```
Creates: **6 topics** + **7 journal entries** + **4 chat sessions** in ~10 seconds

### 2. **AI-Powered Demo**
Small AI-generated sample:
```bash
python demo_ai_populate.py
```
Creates: **10 topics** + **3 AI journal entries** + **2 AI chat sessions** in ~3 minutes

### 3. **Full AI Population**
Large-scale AI-generated content:
```bash
python populate_data.py --journal-entries 20 --chat-sessions 10
```
Creates: **10 topics** + **20 AI journal entries** + **10 AI chat sessions** in ~15 minutes

## 🌍 New Features

### ✨ Multilingual Support
- **English 🇺🇸** and **German 🇩🇪** content
- Tests multilingual auto-tagging
- Validates sentiment analysis across languages
- Language-specific AI prompting

### 📚 Topic Integration
- **Automatic topic creation** in both languages
- **Smart categorization** of entries to appropriate topics
- **Topics created**:
  - Work & Career / Arbeit & Karriere
  - Personal Growth / Persönliche Entwicklung  
  - Family & Relationships / Familie & Beziehungen
  - Health & Wellness / Gesundheit & Wohlbefinden
  - Travel & Adventure / Reisen & Abenteuer

### 🎯 Enhanced Content
- **German journal entries**: Authentic German reflections
- **German chat sessions**: Natural German conversations
- **Topic assignment**: Entries automatically categorized
- **Cultural authenticity**: Language-appropriate themes and expressions

## Prerequisites

### For Quick Populate (No setup needed)
- Backend running on `http://localhost:8000`
- Python with `aiohttp` installed

### For AI-Powered Scripts
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

## Usage Examples

### Quick Testing
```bash
# Fast predefined content (recommended for demos)
python quick_populate.py

# Output:
# 🚀 Quick population starting...
# 📚 Creating topics...
# ✅ Created topic: 'Work & Career' (en)
# ✅ Created topic: 'Arbeit & Karriere' (de)
# ...
# ✅ Created: 'Productive Monday' 🇺🇸
# ✅ Created: 'Arbeitsreiche Woche' 🇩🇪
# ...
# 🌍 Multilingual data: English 🇺🇸 and German 🇩🇪
```

### AI-Generated Content
```bash
# Small AI sample
python demo_ai_populate.py

# Custom amounts
python populate_data.py --journal-entries 15 --chat-sessions 8

# Just journals
python populate_data.py --journal-entries 25 --chat-sessions 0

# Just chats
python populate_data.py --journal-entries 0 --chat-sessions 15
```

## What Gets Created

### Journal Entries
- **Realistic multilingual content**: Personal reflections in English and German
- **Variety of topics**: Work, family, health, creativity, travel, personal growth
- **Natural language**: Authentic emotions and cultural expressions
- **Auto-tagging**: Leverages your app's automatic tagging system
- **Topic categorization**: Smart assignment to appropriate topics
- **Date distribution**: Spread across the last 30 days

### Chat Sessions
- **Different session types**: Reflection Buddy, Inner Voice, Growth Challenge, Pattern Detective, Free Chat
- **Multilingual conversations**: Natural dialogues in both languages
- **Variety of themes**: Personal growth, relationships, decision-making, stress management
- **Realistic flow**: Questions, responses, and follow-ups
- **Auto-tagging**: Tags generated based on conversation content

### Topics
- **Bilingual topics**: Created in both English and German
- **Smart categorization**: Entries automatically assigned to relevant topics
- **Comprehensive coverage**: Work, relationships, health, travel, personal growth

## Expected Output

### Quick Populate
```
🚀 Quick population starting...
📚 Creating topics...
✅ Created topic: 'Work & Career' (en)
✅ Created topic: 'Arbeit & Karriere' (de)
✅ Created topic: 'Personal Growth' (en)
...

📝 Creating 7 journal entries...
✅ Created: 'Productive Monday' 🇺🇸
   Tags: ['productivity', 'motivation', 'confidence', 'teamwork']
✅ Created: 'Arbeitsreiche Woche' 🇩🇪  
   Tags: ['workload', 'accomplishment', 'prioritization', 'boundaries']
...

💬 Creating 4 sample chat sessions...
✅ Created session: 'Work Stress Discussion' 🇺🇸
   Tags: ['work stress', 'prioritization', 'anxiety', 'overwhelm']
✅ Created session: 'Selbstreflexion über Beziehungen' 🇩🇪
   Tags: ['friendship', 'time management', 'guilt', 'loneliness']
...

✨ Quick population complete!
🎯 Created 6 topics + 7 journal entries + 4 chat sessions
🌍 Multilingual data: English 🇺🇸 and German 🇩🇪
📚 Topics with categorized entries
```

### AI-Powered Populate
```
🚀 Starting data population...
📚 Creating 10 topics
📝 Generating 15 journal entries  
💬 Generating 8 chat sessions
🌍 Languages: English 🇺🇸 and German 🇩🇪

� Creating topics...
✅ Created topic: 'Work & Career' 🇺🇸
✅ Created topic: 'Arbeit & Karriere' 🇩🇪
...

�📝 Creating journal entries...
   Generating entry 1/15: work stress and productivity (en)
✅ Created journal entry: 'Monday Overwhelm' 🇺🇸
   Auto-generated tags: ['stress', 'productivity', 'deadlines', 'motivation']
   Generating entry 2/15: kreative Projekte und Hobbys (de)
✅ Created journal entry: 'Kreativität entdecken' 🇩🇪
   Auto-generated tags: ['kreativität', 'inspiration', 'hobbys', 'leidenschaft']
...

✨ Data population complete!
🎯 Created 10 topics + 15 journal entries + 8 chat sessions
🌍 Multilingual content testing (English 🇺🇸 and German 🇩🇪)
```

## Testing the Results

After running any script, you can:

1. **View topics** - See categorized entries in both languages
2. **Check multilingual analytics** - Mood trends across languages  
3. **Test auto-tagging** - See how AI categorizes German vs English content
4. **Explore coaching suggestions** - Based on multilingual content
5. **Try chat in German** - Ask questions about German entries
6. **Validate sentiment analysis** - Check accuracy across languages

## Troubleshooting

### "Connection refused" errors
- Make sure backend is running: `cd backend && python run.py`
- Check API accessibility: `curl http://localhost:8000/api/v1/entries/`

### Ollama errors (AI-powered scripts only)
- Ensure Ollama is running: `ollama list` should show `llama3.1`
- If model missing: `ollama pull llama3.1`
- Check Ollama port: `http://localhost:11434`

### Topic creation errors
- Topics API might not exist yet - check backend logs
- Try quick_populate.py first to test topic functionality

### German content issues
- Auto-tagging should work with German content
- If tags are in English, that's expected (AI might translate)
- Sentiment analysis should work across languages

## Performance Notes

- **Quick populate**: ~10 seconds (predefined content)
- **AI demo**: ~3 minutes (small AI generation)
- **Full AI populate**: ~15-20 minutes for 20 entries + 10 sessions
- **German generation**: Same speed as English (Ollama handles both)
- **Topic creation**: Adds ~5 seconds total

## Customization

### Adding Languages
To add more languages, extend the theme arrays in `populate_data.py`:
```python
{"theme": "travail et productivité", "language": "fr"},  # French
{"theme": "trabajo y productividad", "language": "es"},  # Spanish
```

### Adding Topics
Add new topic categories to the `topics` array:
```python
{"name": "Creativity & Art", "description": "...", "language": "en"},
{"name": "Kreativität & Kunst", "description": "...", "language": "de"}
```

### Changing AI Model
Update the model name in `populate_data.py`:
```python
model="llama3.2"  # or any other Ollama model
```

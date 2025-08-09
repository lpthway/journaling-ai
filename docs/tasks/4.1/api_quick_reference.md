# AI Journaling Assistant - API Quick Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/entries
```

## Quick Commands

### Journal Entries
```bash
# Create entry
POST /entries
{"title":"My Day","content":"Had a great day!","tags":["positive"]}

# Get all entries  
GET /entries?limit=10&mood=joy

# Search entries
GET /entries/search?q=learning

# Get single entry
GET /entries/{id}

# Update entry
PUT /entries/{id}
{"title":"Updated Title","content":"Updated content"}

# Delete entry
DELETE /entries/{id}
```

### Chat Sessions
```bash
# Create session
POST /sessions  
{"type":"coaching","title":"Career Talk","context":"Career discussion"}

# Send message
POST /sessions/{id}/messages
{"content":"I need career advice","role":"user"}

# Get messages
GET /sessions/{id}/messages
```

### Topics
```bash
# Create topic
POST /topics
{"name":"Personal Growth","description":"Self-improvement","color":"#4CAF50"}

# Get all topics
GET /topics
```

### AI Insights  
```bash
# Mood analysis
GET /insights/mood-analysis?days=30

# Pattern analysis
GET /insights/patterns?type=topics

# Ask AI
POST /insights/ask
{"question":"What patterns do you see?","context":"mood_analysis"}
```

### Health Monitoring
```bash
# Basic health
GET /health

# Detailed health  
GET /api/v1/health

# Performance health
GET /api/v1/health/performance

# Cache health
GET /api/v1/health/cache
```

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

## Common Headers

### Request Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Response Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1628097600
```

## Data Models

### Entry
```json
{
  "id": "uuid",
  "title": "string",
  "content": "string", 
  "mood": "joy|sadness|anger|fear|surprise|neutral",
  "sentiment_score": 0.85,
  "tags": ["tag1", "tag2"],
  "word_count": 100,
  "created_at": "2025-08-09T10:00:00Z",
  "updated_at": "2025-08-09T10:00:00Z"
}
```

### Session
```json
{
  "id": "uuid",
  "type": "coaching|therapy|general|crisis",
  "title": "string",
  "status": "active|completed|paused", 
  "context": "string",
  "message_count": 5,
  "created_at": "2025-08-09T10:00:00Z"
}
```

### Message  
```json
{
  "id": "uuid",
  "content": "string",
  "role": "user|assistant",
  "emotion_detected": "joy",
  "confidence": 0.78,
  "created_at": "2025-08-09T10:00:00Z"
}
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-secret-key
JWT_EXPIRE_HOURS=24

# AI Services  
OLLAMA_BASE_URL=http://localhost:11434
AI_MODEL_PATH=/path/to/models

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Common Examples

### Complete User Flow
```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123","full_name":"John Doe"}'

# 2. Login  
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}' \
  | jq -r '.access_token')

# 3. Create entry
ENTRY_ID=$(curl -X POST http://localhost:8000/api/v1/entries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"First Entry","content":"Today I started using the API!","tags":["first","api"]}' \
  | jq -r '.id')

# 4. Get entry
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/entries/$ENTRY_ID

# 5. Start chat session
SESSION_ID=$(curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"coaching","title":"API Learning","context":"Learning to use the API"}' \
  | jq -r '.id')

# 6. Send message
curl -X POST http://localhost:8000/api/v1/sessions/$SESSION_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"How can I improve my journaling habits?","role":"user"}'
```

### Batch Operations
```bash
# Get insights for multiple periods
for days in 7 14 30; do
  echo "=== $days days ===" 
  curl -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000/api/v1/insights/mood-analysis?days=$days" \
    | jq '.mood_distribution'
done

# Search multiple terms
for term in learning growth positive; do
  echo "=== $term ===" 
  curl -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000/api/v1/entries/search?q=$term&limit=5" \
    | jq '.results[].title'
done
```

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check if token is included in Authorization header
- Verify token hasn't expired (24 hour default)
- Ensure Bearer prefix is included

**429 Rate Limited**  
- Check X-RateLimit-* headers
- Wait for rate limit reset
- Reduce request frequency

**500 Server Error**
- Check server logs for correlation_id
- Verify all required services (PostgreSQL, Redis) are running
- Check health endpoints

### Debug Commands
```bash
# Check API health
curl http://localhost:8000/health

# Validate token
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq

# Check rate limits
curl -I -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/entries

# Test connectivity
curl -X OPTIONS http://localhost:8000/api/v1/entries
```
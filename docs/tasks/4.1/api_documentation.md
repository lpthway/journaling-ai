# AI Journaling Assistant - API Documentation

**Version**: 2.0.0  
**Base URL**: `http://localhost:8000`  
**API Prefix**: `/api/v1`

## Overview

The AI Journaling Assistant provides a comprehensive REST API for journal entry management, AI-powered insights, chat sessions, and user authentication. The API follows REST principles and returns JSON responses.

## Authentication

The API uses JWT (JSON Web Token) based authentication.

### Base URL
```
POST /api/v1/auth
```

### Endpoints

#### User Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123",
  "full_name": "John Doe"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "user@example.com", 
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-08-09T10:00:00Z"
}
```

#### User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### Token Refresh
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Authentication Headers
For authenticated endpoints, include the JWT token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Journal Entries

### Base URL
```
/api/v1/entries
```

### Endpoints

#### Create Entry
```http
POST /api/v1/entries
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My First Entry",
  "content": "Today was a great day! I learned so much about API development.",
  "topic_id": "uuid-optional",
  "tags": ["learning", "development", "positive"]
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "title": "My First Entry",
  "content": "Today was a great day! I learned so much about API development.",
  "mood": "joy",
  "sentiment_score": 0.85,
  "tags": ["learning", "development", "positive", "growth"],
  "word_count": 12,
  "created_at": "2025-08-09T10:00:00Z",
  "updated_at": "2025-08-09T10:00:00Z",
  "topic_id": "uuid-optional"
}
```

#### Get All Entries
```http
GET /api/v1/entries?limit=20&offset=0&mood=joy&start_date=2025-08-01
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (int): Number of entries to return (default: 20, max: 100)
- `offset` (int): Number of entries to skip (default: 0)
- `mood` (string): Filter by mood (joy, sadness, anger, fear, surprise, neutral)
- `start_date` (date): Filter entries from this date (YYYY-MM-DD)
- `end_date` (date): Filter entries to this date (YYYY-MM-DD)
- `search` (string): Search in entry content and titles
- `tags` (string): Comma-separated list of tags to filter by

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "My First Entry", 
      "content": "Today was a great day!",
      "mood": "joy",
      "sentiment_score": 0.85,
      "tags": ["learning", "development"],
      "word_count": 12,
      "created_at": "2025-08-09T10:00:00Z",
      "updated_at": "2025-08-09T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Single Entry
```http
GET /api/v1/entries/{entry_id}
Authorization: Bearer <token>
```

#### Update Entry
```http
PUT /api/v1/entries/{entry_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content with more details.",
  "tags": ["updated", "learning"]
}
```

#### Delete Entry
```http
DELETE /api/v1/entries/{entry_id}
Authorization: Bearer <token>
```

**Response (204 No Content)**

#### Search Entries
```http
GET /api/v1/entries/search?q=learning&limit=10
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "Learning Day",
      "content": "Today I learned about APIs...",
      "relevance_score": 0.95,
      "mood": "joy",
      "created_at": "2025-08-09T10:00:00Z",
      "highlight": "Today I **learned** about APIs..."
    }
  ],
  "total": 1,
  "query": "learning"
}
```

## Chat Sessions

### Base URL
```
/api/v1/sessions
```

### Endpoints

#### Create Session
```http
POST /api/v1/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "coaching",
  "title": "Career Discussion",
  "context": "I want to discuss my career goals"
}
```

**Session Types:**
- `coaching` - Life coaching conversations
- `therapy` - Therapeutic support sessions  
- `general` - General chat sessions
- `crisis` - Crisis support sessions

**Response (200 OK):**
```json
{
  "id": "uuid",
  "type": "coaching", 
  "title": "Career Discussion",
  "status": "active",
  "context": "I want to discuss my career goals",
  "created_at": "2025-08-09T10:00:00Z",
  "updated_at": "2025-08-09T10:00:00Z",
  "message_count": 0
}
```

#### Get All Sessions
```http
GET /api/v1/sessions?type=coaching&status=active
Authorization: Bearer <token>
```

**Query Parameters:**
- `type` (string): Filter by session type
- `status` (string): Filter by status (active, completed, paused)
- `limit` (int): Number of sessions to return
- `offset` (int): Number to skip

#### Send Message
```http
POST /api/v1/sessions/{session_id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "I'm feeling uncertain about my career path. What should I do?",
  "role": "user"
}
```

**Response (200 OK):**
```json
{
  "user_message": {
    "id": "uuid",
    "content": "I'm feeling uncertain about my career path. What should I do?",
    "role": "user",
    "created_at": "2025-08-09T10:00:00Z"
  },
  "ai_response": {
    "id": "uuid", 
    "content": "It's natural to feel uncertain about career paths. Let's explore what aspects of your current situation are causing this uncertainty. What specific areas make you feel most unsure?",
    "role": "assistant",
    "created_at": "2025-08-09T10:00:01Z",
    "reasoning": "The user expressed career uncertainty. I'm using reflective questioning to help them identify specific concerns.",
    "emotion_detected": "anxiety",
    "confidence": 0.78
  },
  "session_updated": true
}
```

#### Get Session Messages
```http
GET /api/v1/sessions/{session_id}/messages?limit=50
Authorization: Bearer <token>
```

## Topics

### Base URL
```
/api/v1/topics
```

### Endpoints

#### Create Topic
```http
POST /api/v1/topics
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Personal Growth",
  "description": "Entries about self-improvement and learning",
  "color": "#4CAF50"
}
```

#### Get All Topics
```http
GET /api/v1/topics
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": "uuid",
    "name": "Personal Growth",
    "description": "Entries about self-improvement", 
    "color": "#4CAF50",
    "entry_count": 5,
    "created_at": "2025-08-09T10:00:00Z"
  }
]
```

## AI Insights

### Base URL
```
/api/v1/insights
```

### Endpoints

#### Get Mood Analysis
```http
GET /api/v1/insights/mood-analysis?days=30
Authorization: Bearer <token>
```

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)
- `start_date` (date): Start date for analysis
- `end_date` (date): End date for analysis

**Response (200 OK):**
```json
{
  "period": {
    "start_date": "2025-07-10",
    "end_date": "2025-08-09", 
    "days": 30
  },
  "mood_distribution": {
    "joy": 45.2,
    "neutral": 32.1,
    "sadness": 12.3,
    "anger": 5.4,
    "fear": 3.2,
    "surprise": 1.8
  },
  "mood_trends": [
    {
      "date": "2025-08-09",
      "average_sentiment": 0.72,
      "dominant_mood": "joy",
      "entry_count": 3
    }
  ],
  "insights": [
    "Your mood has been consistently positive over the last week",
    "You show increased joy when writing about learning and growth"
  ]
}
```

#### Get Pattern Analysis  
```http
GET /api/v1/insights/patterns?type=topics
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "analysis_type": "topics",
  "time_period": "last_30_days",
  "patterns": [
    {
      "pattern": "Learning activities correlate with positive mood",
      "confidence": 0.89,
      "occurrences": 15,
      "suggestion": "Continue engaging in learning activities for mood improvement"
    }
  ],
  "topic_correlations": {
    "Personal Growth": {
      "average_sentiment": 0.78,
      "mood_distribution": {"joy": 60, "neutral": 30, "other": 10}
    }
  }
}
```

#### Ask AI Question
```http
POST /api/v1/insights/ask
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What patterns do you see in my mood over the last month?",
  "context": "mood_analysis",
  "include_suggestions": true
}
```

**Response (200 OK):**
```json
{
  "question": "What patterns do you see in my mood over the last month?",
  "answer": "Based on your entries from the last month, I notice several positive patterns. Your mood tends to be most positive when you write about learning and personal development. You show consistent improvement in emotional regulation, and your entries indicate growing self-awareness.",
  "evidence": [
    "15 entries mentioned learning with average sentiment 0.82",
    "Mood stability increased 23% compared to previous month"
  ],
  "suggestions": [
    "Continue focusing on learning activities",
    "Consider exploring topics that consistently boost your mood"
  ],
  "confidence": 0.87
}
```

## Health Monitoring

### Base URL
```
/health
/api/v1/health
```

### Endpoints

#### Basic Health Check
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "journaling-assistant", 
  "version": "2.0.0",
  "redis_integration": "active"
}
```

#### Detailed Health Check
```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "journaling-assistant",
  "version": "2.0.0", 
  "timestamp": "2025-08-09T10:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "connection_pool": {
        "active": 5,
        "idle": 15,
        "total": 20
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2,
      "hit_rate": 0.85
    },
    "ai_services": {
      "status": "healthy",
      "models_loaded": 7,
      "memory_usage_mb": 1024
    }
  },
  "cache_performance": {
    "hit_rate": 0.85,
    "avg_response_time": 0.003,
    "total_operations": 1500
  }
}
```

## Circuit Breakers

### Base URL
```
/circuit-breakers
```

### Endpoints

#### Get Circuit Breaker Status
```http
GET /circuit-breakers/status
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "circuit_breakers": {
    "ollama_llm": {
      "state": "CLOSED",
      "failure_count": 0,
      "success_count": 150,
      "last_failure": null,
      "next_attempt": null
    }
  },
  "overall_health": "healthy"
}
```

## Error Responses

All endpoints return structured error responses:

### Validation Error (400)
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Entry content must be at least 3 characters long",
  "details": {
    "field": "content",
    "provided_length": 2
  },
  "correlation_id": "uuid"
}
```

### Authentication Error (401)
```json
{
  "error_code": "AUTHENTICATION_REQUIRED", 
  "message": "Valid authentication token required",
  "correlation_id": "uuid"
}
```

### Not Found (404)
```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "Entry not found", 
  "correlation_id": "uuid"
}
```

### Rate Limit (429)
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60,
  "correlation_id": "uuid"
}
```

### Server Error (500)
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred", 
  "correlation_id": "uuid"
}
```

## Rate Limiting

The API implements rate limiting for user protection:

- **Authentication endpoints**: 5 requests per minute
- **Entry creation**: 60 requests per hour  
- **Chat sessions**: 100 messages per hour
- **General endpoints**: 1000 requests per hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1628097600
```

## SDKs and Examples

### Python Example
```python
import requests

# Authentication
auth_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = auth_response.json()['access_token']

# Create entry
headers = {'Authorization': f'Bearer {token}'}
entry_response = requests.post('http://localhost:8000/api/v1/entries', 
    headers=headers,
    json={
        'title': 'My Entry',
        'content': 'Today was a great day for learning about APIs!',
        'tags': ['learning', 'positive']
    }
)
print(entry_response.json())
```

### JavaScript Example
```javascript
// Authentication
const authResponse = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const { access_token } = await authResponse.json();

// Create entry
const entryResponse = await fetch('http://localhost:8000/api/v1/entries', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My Entry',
    content: 'Today was a great day for learning about APIs!',
    tags: ['learning', 'positive']
  })
});
const entry = await entryResponse.json();
console.log(entry);
```

## Webhooks (Future)

The API will support webhooks for real-time notifications:

- `entry.created` - New journal entry created
- `session.completed` - Chat session completed  
- `mood.alert` - Concerning mood patterns detected
- `crisis.detected` - Crisis indicators in content

## OpenAPI Specification

The complete OpenAPI specification is available at:
- **JSON**: `http://localhost:8000/api/v1/openapi.json`
- **Interactive UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`
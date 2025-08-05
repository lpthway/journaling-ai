# API Reference

## Overview

The Journaling AI backend provides a RESTful API built with FastAPI. This reference covers all available endpoints, request/response formats, authentication, and usage examples.

## Base Information

- **Base URL**: `http://localhost:8000` (development) / `https://api.journaling-ai.com` (production)
- **API Version**: v1
- **API Prefix**: `/api/v1`
- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **Content Type**: `application/json`
- **Authentication**: JWT Bearer tokens

## Authentication

### Authentication Flow

#### 1. User Registration
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2025-08-05T10:00:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 2. User Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### 3. Token Refresh
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

### Using Authentication

Include the access token in the `Authorization` header for all authenticated endpoints:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Journal Entries

### Create Journal Entry
```http
POST /api/v1/entries/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My First Journal Entry",
  "content": "Today was a great day. I learned a lot about FastAPI and felt productive.",
  "entry_date": "2025-08-05",
  "mood_score": 0.8,
  "tags": ["productivity", "learning", "technology"]
}
```

**Response (201 Created):**
```json
{
  "id": "456e7890-e12b-34c5-d678-901234567890",
  "title": "My First Journal Entry",
  "content": "Today was a great day. I learned a lot about FastAPI and felt productive.",
  "entry_date": "2025-08-05",
  "mood_score": 0.8,
  "word_count": 15,
  "created_at": "2025-08-05T10:30:00Z",
  "updated_at": "2025-08-05T10:30:00Z",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tags": ["productivity", "learning", "technology"],
  "sentiment_analysis": {
    "overall_sentiment": "positive",
    "confidence": 0.92,
    "emotions": {
      "joy": 0.65,
      "satisfaction": 0.72,
      "excitement": 0.45
    }
  }
}
```

### Get User's Journal Entries
```http
GET /api/v1/entries/?page=1&size=20&sort_by=created_at&order=desc
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 20, max: 100)
- `sort_by` (str): Sort field (created_at, entry_date, mood_score, word_count)
- `order` (str): Sort order (asc, desc)
- `date_from` (date): Filter entries from date
- `date_to` (date): Filter entries to date
- `min_mood` (float): Minimum mood score filter
- `max_mood` (float): Maximum mood score filter
- `search` (str): Search in title and content

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "456e7890-e12b-34c5-d678-901234567890",
      "title": "My First Journal Entry",
      "content": "Today was a great day...",
      "entry_date": "2025-08-05",
      "mood_score": 0.8,
      "word_count": 15,
      "created_at": "2025-08-05T10:30:00Z",
      "updated_at": "2025-08-05T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### Get Single Journal Entry
```http
GET /api/v1/entries/456e7890-e12b-34c5-d678-901234567890
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "456e7890-e12b-34c5-d678-901234567890",
  "title": "My First Journal Entry",
  "content": "Today was a great day. I learned a lot about FastAPI and felt productive.",
  "entry_date": "2025-08-05",
  "mood_score": 0.8,
  "word_count": 15,
  "created_at": "2025-08-05T10:30:00Z",
  "updated_at": "2025-08-05T10:30:00Z",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tags": ["productivity", "learning", "technology"],
  "sentiment_analysis": [
    {
      "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
      "sentiment_label": "positive",
      "confidence_score": 0.92,
      "emotions": {
        "joy": 0.65,
        "satisfaction": 0.72,
        "excitement": 0.45
      },
      "analyzed_at": "2025-08-05T10:30:15Z"
    }
  ],
  "similar_entries": [
    {
      "id": "789e0123-e45f-67g8-h901-234567890123",
      "title": "Another Productive Day",
      "similarity_score": 0.85,
      "entry_date": "2025-08-03"
    }
  ]
}
```

### Update Journal Entry
```http
PUT /api/v1/entries/456e7890-e12b-34c5-d678-901234567890
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Updated Journal Entry",
  "content": "Today was a great day. I learned a lot about FastAPI and felt very productive. I also helped a colleague with their code.",
  "mood_score": 0.9,
  "tags": ["productivity", "learning", "technology", "helping"]
}
```

**Response (200 OK):**
```json
{
  "id": "456e7890-e12b-34c5-d678-901234567890",
  "title": "My Updated Journal Entry",
  "content": "Today was a great day. I learned a lot about FastAPI and felt very productive. I also helped a colleague with their code.",
  "entry_date": "2025-08-05",
  "mood_score": 0.9,
  "word_count": 23,
  "created_at": "2025-08-05T10:30:00Z",
  "updated_at": "2025-08-05T11:15:00Z",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tags": ["productivity", "learning", "technology", "helping"]
}
```

### Delete Journal Entry
```http
DELETE /api/v1/entries/456e7890-e12b-34c5-d678-901234567890
Authorization: Bearer <token>
```

**Response (204 No Content)**

### Search Journal Entries
```http
GET /api/v1/entries/search?q=productive&limit=10
Authorization: Bearer <token>
```

**Query Parameters:**
- `q` (str): Search query (searches title and content)
- `limit` (int): Maximum results (default: 10, max: 50)
- `similarity_threshold` (float): Minimum similarity score (0.0-1.0)

**Response (200 OK):**
```json
{
  "query": "productive",
  "results": [
    {
      "id": "456e7890-e12b-34c5-d678-901234567890",
      "title": "My Updated Journal Entry",
      "content_snippet": "...felt very productive. I also helped...",
      "relevance_score": 0.95,
      "entry_date": "2025-08-05",
      "mood_score": 0.9
    }
  ],
  "total_results": 1,
  "search_time_ms": 45
}
```

## Sentiment Analysis

### Get Sentiment Analysis for Entry
```http
GET /api/v1/sentiment/456e7890-e12b-34c5-d678-901234567890
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "entry_id": "456e7890-e12b-34c5-d678-901234567890",
  "analyses": [
    {
      "id": "sentiment-123",
      "model_name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
      "sentiment_label": "positive",
      "confidence_score": 0.92,
      "emotions": {
        "joy": 0.65,
        "satisfaction": 0.72,
        "excitement": 0.45,
        "sadness": 0.05,
        "anger": 0.02,
        "fear": 0.03
      },
      "analyzed_at": "2025-08-05T10:30:15Z"
    },
    {
      "id": "sentiment-124",
      "model_name": "j-hartmann/emotion-english-distilroberta-base",
      "sentiment_label": "joy",
      "confidence_score": 0.78,
      "emotions": {
        "joy": 0.78,
        "optimism": 0.65,
        "love": 0.12,
        "surprise": 0.08,
        "sadness": 0.03,
        "anger": 0.01,
        "fear": 0.02,
        "disgust": 0.01
      },
      "analyzed_at": "2025-08-05T10:30:16Z"
    }
  ]
}
```

### Reanalyze Entry Sentiment
```http
POST /api/v1/sentiment/456e7890-e12b-34c5-d678-901234567890/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "models": ["cardiffnlp/twitter-roberta-base-sentiment-latest", "j-hartmann/emotion-english-distilroberta-base"],
  "force_refresh": true
}
```

**Response (200 OK):**
```json
{
  "entry_id": "456e7890-e12b-34c5-d678-901234567890",
  "status": "completed",
  "analyses_updated": 2,
  "processing_time_ms": 1250
}
```

## Psychology Insights

### Get User Psychology Insights
```http
GET /api/v1/psychology/insights
Authorization: Bearer <token>
```

**Query Parameters:**
- `insight_type` (str): Filter by insight type (mood_patterns, writing_style, emotional_trends, etc.)
- `date_from` (date): Filter insights from date
- `date_to` (date): Filter insights to date
- `active_only` (bool): Show only active insights (default: true)

**Response (200 OK):**
```json
{
  "insights": [
    {
      "id": "insight-789",
      "insight_type": "mood_patterns",
      "insight_data": {
        "pattern_type": "weekly_cycle",
        "description": "Your mood tends to be highest on weekends and lowest on Mondays",
        "confidence": 0.85,
        "data_points": 45,
        "trend": "improving",
        "recommendations": [
          "Consider planning relaxing activities for Sunday evenings",
          "Schedule lighter workloads on Mondays when possible"
        ]
      },
      "confidence_level": 0.85,
      "generated_at": "2025-08-05T09:00:00Z",
      "is_active": true
    },
    {
      "id": "insight-790",
      "insight_type": "emotional_trends",
      "insight_data": {
        "dominant_emotions": ["joy", "satisfaction", "excitement"],
        "emotion_stability": 0.78,
        "emotional_range": "moderate",
        "recent_changes": {
          "trend": "more_positive",
          "since": "2025-07-20",
          "factors": ["increased_exercise", "better_sleep"]
        }
      },
      "confidence_level": 0.79,
      "generated_at": "2025-08-05T09:00:00Z",
      "is_active": true
    }
  ]
}
```

### Generate New Psychology Insights
```http
POST /api/v1/psychology/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "analysis_types": ["mood_patterns", "emotional_trends", "writing_style"],
  "date_range_days": 90,
  "min_entries": 10
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "analysis-task-456",
  "status": "processing",
  "estimated_completion": "2025-08-05T10:35:00Z",
  "analysis_types": ["mood_patterns", "emotional_trends", "writing_style"]
}
```

### Get Psychology Analysis Status
```http
GET /api/v1/psychology/analyze/analysis-task-456
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "task_id": "analysis-task-456",
  "status": "completed",
  "progress": 100,
  "insights_generated": 3,
  "processing_time_ms": 15750,
  "completed_at": "2025-08-05T10:33:45Z"
}
```

## Topics and Tags

### Get User Topics
```http
GET /api/v1/topics/
Authorization: Bearer <token>
```

**Query Parameters:**
- `include_system` (bool): Include system-generated topics (default: true)
- `sort_by` (str): Sort by name, created_at, entry_count
- `search` (str): Search topic names

**Response (200 OK):**
```json
{
  "topics": [
    {
      "id": "topic-123",
      "name": "Work & Career",
      "description": "Professional life, career goals, work challenges and achievements",
      "is_system_topic": true,
      "entry_count": 23,
      "created_at": "2025-08-01T00:00:00Z",
      "recent_relevance": 0.85
    },
    {
      "id": "topic-124",
      "name": "Personal Growth",
      "description": "Self-improvement, learning, skill development",
      "is_system_topic": false,
      "entry_count": 18,
      "created_at": "2025-08-02T10:15:00Z",
      "recent_relevance": 0.92
    }
  ]
}
```

### Create Custom Topic
```http
POST /api/v1/topics/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Fitness Journey",
  "description": "My fitness goals, workouts, and health improvements"
}
```

**Response (201 Created):**
```json
{
  "id": "topic-125",
  "name": "Fitness Journey",
  "description": "My fitness goals, workouts, and health improvements",
  "is_system_topic": false,
  "entry_count": 0,
  "created_at": "2025-08-05T11:00:00Z",
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Get Topic Suggestions
```http
GET /api/v1/topics/suggestions?entry_text=Today I went to the gym and had a great workout
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "suggestions": [
    {
      "topic_name": "Fitness Journey",
      "relevance_score": 0.94,
      "is_existing": true,
      "topic_id": "topic-125"
    },
    {
      "topic_name": "Health & Wellness",
      "relevance_score": 0.87,
      "is_existing": true,
      "topic_id": "topic-102"
    },
    {
      "topic_name": "Exercise & Movement",
      "relevance_score": 0.82,
      "is_existing": false,
      "suggested_description": "Physical activities, exercise routines, and movement practices"
    }
  ]
}
```

## Analytics and Statistics

### Get User Analytics Dashboard
```http
GET /api/v1/analytics/dashboard
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` (str): Time period (7d, 30d, 90d, 1y, all)
- `timezone` (str): User timezone (default: UTC)

**Response (200 OK):**
```json
{
  "period": "30d",
  "summary": {
    "total_entries": 25,
    "total_words": 12450,
    "avg_words_per_entry": 498,
    "avg_mood_score": 0.72,
    "most_active_day": "Sunday",
    "longest_streak": 7,
    "current_streak": 3
  },
  "mood_trends": {
    "daily_averages": [
      {"date": "2025-07-06", "avg_mood": 0.65, "entry_count": 1},
      {"date": "2025-07-07", "avg_mood": 0.78, "entry_count": 2},
      {"date": "2025-07-08", "avg_mood": 0.82, "entry_count": 1}
    ],
    "weekly_pattern": {
      "Monday": 0.68,
      "Tuesday": 0.71,
      "Wednesday": 0.69,
      "Thursday": 0.74,
      "Friday": 0.79,
      "Saturday": 0.85,
      "Sunday": 0.88
    }
  },
  "writing_patterns": {
    "preferred_writing_times": [
      {"hour": 9, "entry_count": 8, "avg_mood": 0.75},
      {"hour": 21, "entry_count": 12, "avg_mood": 0.70}
    ],
    "word_count_distribution": {
      "short": {"range": "1-200", "count": 5, "percentage": 20},
      "medium": {"range": "201-500", "count": 15, "percentage": 60},
      "long": {"range": "501+", "count": 5, "percentage": 20}
    }
  },
  "emotional_analysis": {
    "dominant_emotions": [
      {"emotion": "joy", "frequency": 0.35, "avg_intensity": 0.72},
      {"emotion": "satisfaction", "frequency": 0.28, "avg_intensity": 0.68},
      {"emotion": "excitement", "frequency": 0.15, "avg_intensity": 0.81}
    ],
    "emotion_stability": 0.76,
    "emotional_range": "moderate"
  },
  "topics_analysis": {
    "most_frequent_topics": [
      {"topic": "Work & Career", "entry_count": 12, "avg_mood": 0.68},
      {"topic": "Personal Growth", "entry_count": 8, "avg_mood": 0.82},
      {"topic": "Relationships", "entry_count": 6, "avg_mood": 0.75}
    ]
  }
}
```

### Get Mood Trends
```http
GET /api/v1/analytics/mood-trends?period=30d&granularity=daily
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` (str): Time period (7d, 30d, 90d, 1y)
- `granularity` (str): Data granularity (daily, weekly, monthly)

**Response (200 OK):**
```json
{
  "period": "30d",
  "granularity": "daily",
  "data_points": [
    {
      "date": "2025-07-06",
      "avg_mood": 0.65,
      "min_mood": 0.45,
      "max_mood": 0.85,
      "entry_count": 1,
      "dominant_emotions": ["satisfaction", "calm"]
    },
    {
      "date": "2025-07-07",
      "avg_mood": 0.78,
      "min_mood": 0.70,
      "max_mood": 0.85,
      "entry_count": 2,
      "dominant_emotions": ["joy", "excitement"]
    }
  ],
  "statistics": {
    "average_mood": 0.72,
    "mood_stability": 0.84,
    "improvement_trend": 0.15,
    "best_day": {"date": "2025-08-03", "mood": 0.95},
    "challenging_day": {"date": "2025-07-12", "mood": 0.35}
  }
}
```

## User Management

### Get Current User Profile
```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2025-08-01T10:00:00Z",
  "updated_at": "2025-08-05T11:00:00Z",
  "profile": {
    "timezone": "America/New_York",
    "preferred_language": "en",
    "notification_preferences": {
      "email_reminders": true,
      "weekly_insights": true,
      "mood_alerts": false
    },
    "privacy_settings": {
      "data_sharing": false,
      "analytics_participation": true
    }
  },
  "statistics": {
    "total_entries": 25,
    "account_age_days": 4,
    "current_streak": 3,
    "longest_streak": 7
  }
}
```

### Update User Profile
```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "profile": {
    "timezone": "America/Los_Angeles",
    "preferred_language": "en",
    "notification_preferences": {
      "email_reminders": false,
      "weekly_insights": true,
      "mood_alerts": true
    }
  }
}
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Smith",
  "is_active": true,
  "created_at": "2025-08-01T10:00:00Z",
  "updated_at": "2025-08-05T11:30:00Z",
  "profile": {
    "timezone": "America/Los_Angeles",
    "preferred_language": "en",
    "notification_preferences": {
      "email_reminders": false,
      "weekly_insights": true,
      "mood_alerts": true
    }
  }
}
```

### Change Password
```http
POST /api/v1/users/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password updated successfully"
}
```

## Data Export

### Request Data Export
```http
POST /api/v1/export/request
Authorization: Bearer <token>
Content-Type: application/json

{
  "format": "json",
  "include_sentiment": true,
  "include_analytics": false,
  "date_from": "2025-07-01",
  "date_to": "2025-08-05"
}
```

**Response (202 Accepted):**
```json
{
  "export_id": "export-789",
  "status": "processing",
  "estimated_completion": "2025-08-05T11:45:00Z",
  "format": "json",
  "estimated_size_mb": 2.5
}
```

### Check Export Status
```http
GET /api/v1/export/export-789/status
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "export_id": "export-789",
  "status": "completed",
  "download_url": "/api/v1/export/export-789/download",
  "expires_at": "2025-08-12T11:40:00Z",
  "file_size_mb": 2.3,
  "entry_count": 25,
  "completed_at": "2025-08-05T11:40:00Z"
}
```

### Download Export
```http
GET /api/v1/export/export-789/download
Authorization: Bearer <token>
```

**Response (200 OK):**
```
Content-Type: application/json
Content-Disposition: attachment; filename="journaling_data_2025-08-05.json"

[Binary file content]
```

## System Endpoints

### Health Check
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-05T12:00:00Z",
  "version": "2.1.0",
  "environment": "production",
  "checks": {
    "database": {"status": "healthy", "response_time_ms": 12},
    "redis": {"status": "healthy", "response_time_ms": 3},
    "ai_models": {"status": "healthy", "models_loaded": 8}
  },
  "uptime_seconds": 86400
}
```

### API Information
```http
GET /api/v1/info
```

**Response (200 OK):**
```json
{
  "name": "Journaling AI Backend",
  "version": "2.1.0",
  "api_version": "v1",
  "documentation_url": "/docs",
  "features": {
    "sentiment_analysis": true,
    "psychology_insights": true,
    "data_export": true,
    "advanced_search": true
  },
  "rate_limits": {
    "authenticated": "100/minute",
    "unauthenticated": "10/minute"
  }
}
```

### Model Status
```http
GET /api/v1/models/status
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "models_loaded": 8,
  "models": [
    {
      "name": "cardiffnlp/twitter-roberta-base-sentiment-latest",
      "type": "sentiment",
      "status": "loaded",
      "memory_usage_mb": 450,
      "last_used": "2025-08-05T11:55:00Z"
    },
    {
      "name": "sentence-transformers/all-MiniLM-L6-v2",
      "type": "embedding",
      "status": "loaded",
      "memory_usage_mb": 90,
      "last_used": "2025-08-05T11:58:00Z"
    }
  ],
  "total_memory_usage_mb": 1250,
  "cache_hit_rate": 0.78
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ],
    "timestamp": "2025-08-05T12:00:00Z",
    "request_id": "req-12345"
  }
}
```

### Common Error Codes

#### Authentication Errors (401)
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "The provided access token is invalid or expired",
    "timestamp": "2025-08-05T12:00:00Z"
  }
}
```

#### Authorization Errors (403)
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "You do not have permission to access this resource",
    "timestamp": "2025-08-05T12:00:00Z"
  }
}
```

#### Resource Not Found (404)
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested journal entry was not found",
    "resource_type": "journal_entry",
    "resource_id": "456e7890-e12b-34c5-d678-901234567890",
    "timestamp": "2025-08-05T12:00:00Z"
  }
}
```

#### Rate Limiting (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after_seconds": 60,
    "limit": "100/minute",
    "timestamp": "2025-08-05T12:00:00Z"
  }
}
```

#### Server Error (500)
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "error_id": "err-67890",
    "timestamp": "2025-08-05T12:00:00Z"
  }
}
```

## Rate Limiting

### Rate Limit Headers
All API responses include rate limiting headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1691235600
X-RateLimit-Reset-After: 45
```

### Rate Limits by Endpoint Type
- **Authentication**: 5 requests per minute
- **File Upload**: 10 requests per hour
- **AI Processing**: 20 requests per minute
- **General API**: 100 requests per minute
- **Health Check**: 1000 requests per minute

## Webhooks (Future Feature)

### Webhook Events
```json
{
  "event": "entry.sentiment_analyzed",
  "data": {
    "entry_id": "456e7890-e12b-34c5-d678-901234567890",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "sentiment_score": 0.92,
    "emotions": {
      "joy": 0.65,
      "satisfaction": 0.72
    }
  },
  "timestamp": "2025-08-05T12:00:00Z",
  "webhook_id": "webhook-123"
}
```

---

**Document Version**: 1.0  
**Last Updated**: August 5, 2025  
**Review Date**: September 5, 2025  
**Owner**: API Development Team

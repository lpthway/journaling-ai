#!/usr/bin/env python3
"""
OpenAPI Specification Customization for AI Journaling Assistant

This script enhances the auto-generated OpenAPI specification with additional
examples, documentation, and customizations.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

def enhance_openapi_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance the OpenAPI specification with additional examples and documentation."""
    
    # Add servers configuration
    spec["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.journaling-ai.com",
            "description": "Production server"
        }
    ]
    
    # Enhanced info section
    spec["info"]["termsOfService"] = "https://journaling-ai.com/terms"
    spec["info"]["x-logo"] = {
        "url": "https://journaling-ai.com/logo.png",
        "altText": "AI Journaling Assistant"
    }
    
    # Add security schemes
    if "components" not in spec:
        spec["components"] = {}
    
    spec["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from login endpoint"
        }
    }
    
    # Add global security requirement
    spec["security"] = [{"BearerAuth": []}]
    
    # Enhanced examples for common operations
    examples = {
        "EntryCreate": {
            "summary": "Create a personal journal entry",
            "value": {
                "title": "My Amazing Day",
                "content": "Today was incredible! I learned so much about FastAPI and OpenAPI documentation. The automatic generation is fantastic, and I'm excited to build more features.",
                "tags": ["learning", "technology", "positive"],
                "topic_id": None
            }
        },
        "SessionCreate": {
            "summary": "Start a coaching session", 
            "value": {
                "type": "coaching",
                "title": "Career Development Discussion",
                "context": "I want to discuss my career goals and get guidance on next steps in my professional development."
            }
        },
        "MessageCreate": {
            "summary": "Send a message to AI coach",
            "value": {
                "content": "I'm feeling stuck in my current role and unsure about what direction to take my career. Can you help me think through my options?",
                "role": "user"
            }
        },
        "TopicCreate": {
            "summary": "Create an organization topic",
            "value": {
                "name": "Personal Growth",
                "description": "Entries about self-improvement, learning, and personal development",
                "color": "#4CAF50"
            }
        }
    }
    
    # Add examples to components
    if "examples" not in spec["components"]:
        spec["components"]["examples"] = {}
    spec["components"]["examples"].update(examples)
    
    # Add response examples
    response_examples = {
        "EntryResponse": {
            "summary": "Created journal entry with AI analysis",
            "value": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "My Amazing Day",
                "content": "Today was incredible! I learned so much about FastAPI...",
                "mood": "joy",
                "sentiment_score": 0.92,
                "tags": ["learning", "technology", "positive", "growth"],
                "word_count": 45,
                "created_at": "2025-08-09T10:30:00Z",
                "updated_at": "2025-08-09T10:30:00Z",
                "topic_id": None
            }
        },
        "SessionResponse": {
            "summary": "Active coaching session",
            "value": {
                "id": "660e8400-e29b-41d4-a716-446655440001", 
                "type": "coaching",
                "title": "Career Development Discussion",
                "status": "active",
                "context": "I want to discuss my career goals...",
                "message_count": 0,
                "created_at": "2025-08-09T10:30:00Z",
                "updated_at": "2025-08-09T10:30:00Z"
            }
        },
        "MoodAnalysisResponse": {
            "summary": "30-day mood analysis results",
            "value": {
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
                "insights": [
                    "Your mood has been consistently positive over the last week",
                    "You show increased joy when writing about learning and growth topics"
                ]
            }
        }
    }
    
    spec["components"]["examples"].update(response_examples)
    
    # Add common error responses
    error_responses = {
        "ValidationError": {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error_code": {"type": "string"},
                            "message": {"type": "string"},
                            "details": {"type": "object"},
                            "correlation_id": {"type": "string"}
                        }
                    },
                    "example": {
                        "error_code": "VALIDATION_ERROR",
                        "message": "Entry content must be at least 3 characters long",
                        "details": {"field": "content", "provided_length": 2},
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                }
            }
        },
        "UnauthorizedError": {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object", 
                        "properties": {
                            "error_code": {"type": "string"},
                            "message": {"type": "string"},
                            "correlation_id": {"type": "string"}
                        }
                    },
                    "example": {
                        "error_code": "AUTHENTICATION_REQUIRED",
                        "message": "Valid authentication token required",
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440001"
                    }
                }
            }
        },
        "RateLimitError": {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error_code": {"type": "string"},
                            "message": {"type": "string"},
                            "retry_after": {"type": "integer"},
                            "correlation_id": {"type": "string"}
                        }
                    },
                    "example": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": 60,
                        "correlation_id": "550e8400-e29b-41d4-a716-446655440002"
                    }
                }
            }
        }
    }
    
    # Add responses to components
    if "responses" not in spec["components"]:
        spec["components"]["responses"] = {}
    spec["components"]["responses"].update(error_responses)
    
    return spec

def save_enhanced_spec(spec: Dict[str, Any], output_dir: Path):
    """Save the enhanced specification in multiple formats."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    with open(output_dir / "openapi.json", "w") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    # Save as YAML
    with open(output_dir / "openapi.yaml", "w") as f:
        yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Enhanced OpenAPI specification saved to {output_dir}")

def generate_postman_collection(spec: Dict[str, Any], output_dir: Path):
    """Generate a Postman collection from the OpenAPI spec."""
    collection = {
        "info": {
            "name": spec["info"]["title"],
            "description": spec["info"]["description"],
            "version": spec["info"]["version"],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{access_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "access_token", 
                "value": "",
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Add basic request examples
    auth_folder = {
        "name": "Authentication",
        "item": [
            {
                "name": "Login",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "email": "user@example.com",
                            "password": "password"
                        }, indent=2)
                    },
                    "url": "{{base_url}}/api/v1/auth/login"
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "exec": [
                                "if (pm.response.code === 200) {",
                                "    const responseJson = pm.response.json();", 
                                "    pm.collectionVariables.set('access_token', responseJson.access_token);",
                                "}"
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    entries_folder = {
        "name": "Journal Entries",
        "item": [
            {
                "name": "Create Entry",
                "request": {
                    "method": "POST",
                    "header": [{"key": "Content-Type", "value": "application/json"}],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "title": "My Journal Entry",
                            "content": "Today was a great day for learning about APIs!",
                            "tags": ["learning", "positive"]
                        }, indent=2)
                    },
                    "url": "{{base_url}}/api/v1/entries"
                }
            },
            {
                "name": "Get All Entries",
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/api/v1/entries"
                }
            }
        ]
    }
    
    collection["item"] = [auth_folder, entries_folder]
    
    # Save Postman collection
    with open(output_dir / "postman_collection.json", "w") as f:
        json.dump(collection, f, indent=2)
    
    print(f"Postman collection saved to {output_dir / 'postman_collection.json'}")

if __name__ == "__main__":
    # This would typically fetch the spec from the running server
    # For now, create a basic structure
    base_spec = {
        "openapi": "3.0.2",
        "info": {
            "title": "AI Journaling Assistant",
            "version": "2.0.0",
            "description": "Enterprise-grade journaling and coaching assistant"
        },
        "paths": {},
        "components": {}
    }
    
    # Enhance the specification
    enhanced_spec = enhance_openapi_spec(base_spec)
    
    # Save outputs
    output_dir = Path(__file__).parent / "generated"
    save_enhanced_spec(enhanced_spec, output_dir)
    generate_postman_collection(enhanced_spec, output_dir)
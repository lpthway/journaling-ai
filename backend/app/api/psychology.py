# backend/app/api/psychology.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.psychology_knowledge_service import (
    psychology_knowledge_service, 
    PsychologyDomain
)
from app.services.psychology_data_loader import PsychologyDataLoader
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search")
async def search_psychology_knowledge(
    query: str = Query(..., min_length=1, description="Search query for psychology knowledge"),
    domain: Optional[str] = Query(None, description="Psychology domain to search within"),
    evidence_level: Optional[str] = Query(None, description="Evidence level filter (high, medium, low)"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of results"),
    min_credibility: float = Query(0.5, ge=0.0, le=1.0, description="Minimum credibility score")
):
    """Search psychology knowledge database with filters"""
    try:
        # Validate domain if provided
        psychology_domain = None
        if domain:
            try:
                psychology_domain = PsychologyDomain(domain)
            except ValueError:
                available_domains = [d.value for d in PsychologyDomain]
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid domain. Available: {available_domains}"
                )
        
        # Search knowledge
        results = await psychology_knowledge_service.search_knowledge(
            query=query,
            domain=psychology_domain,
            evidence_level=evidence_level,
            limit=limit,
            min_credibility=min_credibility
        )
        
        return {
            "query": query,
            "filters": {
                "domain": domain,
                "evidence_level": evidence_level,
                "min_credibility": min_credibility
            },
            "results": results,
            "total_found": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching psychology knowledge: {e}")
        raise HTTPException(status_code=500, detail="Failed to search psychology knowledge")

@router.get("/techniques/{issue_type}")
async def get_techniques_for_issue(
    issue_type: str,
    limit: int = Query(5, ge=1, le=10, description="Maximum number of techniques")
):
    """Get specific psychological techniques for a given issue type"""
    try:
        techniques = await psychology_knowledge_service.get_techniques_for_issue(issue_type)
        
        return {
            "issue_type": issue_type,
            "techniques": techniques[:limit],
            "total_found": len(techniques)
        }
        
    except Exception as e:
        logger.error(f"Error getting techniques for issue: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve techniques")

@router.get("/domains")
async def get_available_domains():
    """Get list of available psychology domains"""
    try:
        domains = []
        for domain in PsychologyDomain:
            domains.append({
                "value": domain.value,
                "name": domain.value.replace('_', ' ').title(),
                "description": _get_domain_description(domain)
            })
        
        return {
            "domains": domains,
            "total_count": len(domains)
        }
        
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve domains")

@router.get("/stats")
async def get_database_stats():
    """Get psychology knowledge database statistics"""
    try:
        stats = await psychology_knowledge_service.get_collection_stats()
        
        return {
            "database_stats": stats,
            "domains_info": {
                domain.value: {
                    "name": domain.value.replace('_', ' ').title(),
                    "count": stats.get('domain_breakdown', {}).get(domain.value, 0)
                }
                for domain in PsychologyDomain
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.post("/load-knowledge")
async def load_psychology_knowledge():
    """Load psychology knowledge into the database (admin endpoint)"""
    try:
        loader = PsychologyDataLoader()
        count = await loader.load_all_psychology_knowledge()
        
        return {
            "message": "Psychology knowledge loaded successfully",
            "entries_loaded": count,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error loading psychology knowledge: {e}")
        raise HTTPException(status_code=500, detail="Failed to load psychology knowledge")

@router.get("/context/{user_message}")
async def get_psychology_context(
    user_message: str,
    max_sources: int = Query(3, ge=1, le=10, description="Maximum number of sources"),
    preferred_domains: Optional[str] = Query(None, description="Comma-separated list of preferred domains")
):
    """Get relevant psychology knowledge for AI conversation context"""
    try:
        # Parse preferred domains if provided
        domains = None
        if preferred_domains:
            domain_values = [d.strip() for d in preferred_domains.split(',')]
            domains = []
            for domain_value in domain_values:
                try:
                    domains.append(PsychologyDomain(domain_value))
                except ValueError:
                    continue  # Skip invalid domains
        
        # Get psychology context
        context = await psychology_knowledge_service.get_knowledge_for_context(
            user_message=user_message,
            preferred_domains=domains,
            max_sources=max_sources
        )
        
        return {
            "user_message": user_message,
            "psychology_context": context,
            "sources_found": len(context),
            "domains_searched": [d.value for d in domains] if domains else "all"
        }
        
    except Exception as e:
        logger.error(f"Error getting psychology context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get psychology context")

@router.get("/citation/{source_id}")
async def get_formatted_citation(source_id: str):
    """Get formatted citation for a psychology source"""
    try:
        # This would need to be implemented to retrieve specific source by ID
        # For now, return a placeholder response
        return {
            "source_id": source_id,
            "message": "Citation formatting endpoint - implementation needed",
            "status": "placeholder"
        }
        
    except Exception as e:
        logger.error(f"Error getting citation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get citation")

@router.post("/evaluate-message")
async def evaluate_message_for_psychology_needs(
    message: str,
    conversation_context: Optional[str] = None
):
    """Evaluate a user message to determine what psychology knowledge might be helpful"""
    try:
        # Get relevant psychology knowledge
        psychology_sources = await psychology_knowledge_service.get_knowledge_for_context(
            user_message=message,
            journal_context=conversation_context,
            max_sources=5
        )
        
        # Analyze the types of issues or themes present
        detected_themes = _detect_psychological_themes(message)
        recommended_domains = _recommend_domains_for_themes(detected_themes)
        
        return {
            "message": message,
            "detected_themes": detected_themes,
            "recommended_domains": [domain.value for domain in recommended_domains],
            "relevant_psychology_sources": psychology_sources,
            "analysis": {
                "needs_psychology_support": len(psychology_sources) > 0,
                "confidence_score": min(len(psychology_sources) * 0.2, 1.0),
                "primary_domain": psychology_sources[0]['domain'] if psychology_sources else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error evaluating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate message")

def _get_domain_description(domain: PsychologyDomain) -> str:
    """Get description for a psychology domain"""
    descriptions = {
        PsychologyDomain.CBT: "Cognitive Behavioral Therapy techniques and methods",
        PsychologyDomain.GAMING_PSYCHOLOGY: "Gaming behavior, digital wellness, and technology-related issues",
        PsychologyDomain.ADDICTION_RECOVERY: "Addiction recovery strategies and substance abuse treatment",
        PsychologyDomain.MINDFULNESS: "Mindfulness practices, meditation, and present-moment awareness",
        PsychologyDomain.CRISIS_INTERVENTION: "Crisis response protocols and safety interventions",
        PsychologyDomain.EMOTIONAL_REGULATION: "Emotional management and regulation techniques",
        PsychologyDomain.STRESS_MANAGEMENT: "Stress reduction and coping strategies",
        PsychologyDomain.HABIT_FORMATION: "Habit building, behavior change, and routine development",
        PsychologyDomain.SOCIAL_PSYCHOLOGY: "Social behavior, relationships, and interpersonal dynamics",
        PsychologyDomain.POSITIVE_PSYCHOLOGY: "Wellbeing, happiness, and human flourishing"
    }
    return descriptions.get(domain, "Specialized psychology knowledge domain")

def _detect_psychological_themes(message: str) -> List[str]:
    """Detect psychological themes in a user message"""
    message_lower = message.lower()
    themes = []
    
    # Define theme keywords
    theme_keywords = {
        "anxiety": ["anxious", "worried", "nervous", "panic", "fear", "overwhelmed"],
        "depression": ["sad", "depressed", "hopeless", "worthless", "empty", "down"],
        "stress": ["stressed", "pressure", "overwhelmed", "burned out", "tense"],
        "gaming": ["gaming", "video games", "gaming addiction", "too much gaming", "game"],
        "addiction": ["addiction", "addicted", "substance", "drinking", "drugs", "habit"],
        "relationships": ["relationship", "family", "friends", "social", "lonely", "conflict"],
        "work": ["work", "job", "career", "workplace", "boss", "colleagues"],
        "habits": ["habit", "routine", "change", "behavior", "pattern"],
        "crisis": ["crisis", "emergency", "suicide", "self-harm", "danger", "help"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            themes.append(theme)
    
    return themes

def _recommend_domains_for_themes(themes: List[str]) -> List[PsychologyDomain]:
    """Recommend psychology domains based on detected themes"""
    domain_mapping = {
        "anxiety": [PsychologyDomain.CBT, PsychologyDomain.MINDFULNESS],
        "depression": [PsychologyDomain.CBT, PsychologyDomain.POSITIVE_PSYCHOLOGY],
        "stress": [PsychologyDomain.STRESS_MANAGEMENT, PsychologyDomain.MINDFULNESS],
        "gaming": [PsychologyDomain.GAMING_PSYCHOLOGY, PsychologyDomain.ADDICTION_RECOVERY],
        "addiction": [PsychologyDomain.ADDICTION_RECOVERY, PsychologyDomain.CBT],
        "relationships": [PsychologyDomain.SOCIAL_PSYCHOLOGY, PsychologyDomain.EMOTIONAL_REGULATION],
        "work": [PsychologyDomain.STRESS_MANAGEMENT, PsychologyDomain.CBT],
        "habits": [PsychologyDomain.HABIT_FORMATION, PsychologyDomain.CBT],
        "crisis": [PsychologyDomain.CRISIS_INTERVENTION, PsychologyDomain.EMOTIONAL_REGULATION]
    }
    
    recommended = []
    for theme in themes:
        if theme in domain_mapping:
            recommended.extend(domain_mapping[theme])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(recommended))
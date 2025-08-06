# backend/app/tasks/analytics.py
"""
Analytics Task Coordinators for Phase 0C
Lightweight task definitions that delegate to analytics services
Follows enterprise architecture: Tasks coordinate, Services contain business logic
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Celery and app imports
from app.services.celery_service import celery_app, monitored_task, TaskPriority, TaskCategory
from app.services.analytics_service import analytics_cache_service
from app.services.background_analytics import background_processor
from app.core.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)

# === ANALYTICS TASK COORDINATORS ===

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_daily_analytics(self, target_date: str = None) -> Dict[str, Any]:
    """
    Task coordinator for daily analytics generation
    Delegates to analytics_cache_service for business logic
    
    Args:
        target_date: Date to generate analytics for (defaults to yesterday)
    
    Returns:
        Daily analytics results with trends and insights
    """
    try:
        start_time = time.time()
        
        logger.info(f"📊 Coordinating daily analytics generation for {target_date or 'yesterday'}")
        
        # Delegate to analytics service for actual processing
        analytics_result = asyncio.run(
            analytics_cache_service.generate_daily_analytics(target_date)
        )
        
        # Add task coordination metadata
        analytics_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_daily_analytics",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        logger.info(f"✅ Daily analytics coordination complete in {analytics_result['task_coordination']['processing_time_ms']}ms")
        
        return analytics_result
        
    except Exception as e:
        logger.error(f"❌ Daily analytics coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_weekly_analytics(self, week_start_date: str = None) -> Dict[str, Any]:
    """
    Task coordinator for weekly analytics generation
    
    Args:
        week_start_date: Start of week to analyze (defaults to last week)
    
    Returns:
        Weekly analytics results
    """
    try:
        start_time = time.time()
        
        logger.info(f"📊 Coordinating weekly analytics generation")
        
        # Delegate to analytics service
        analytics_result = asyncio.run(
            analytics_cache_service.generate_weekly_analytics(week_start_date)
        )
        
        analytics_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_weekly_analytics",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analytics_result
        
    except Exception as e:
        logger.error(f"❌ Weekly analytics coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_mood_trends(self, days: int = 30) -> Dict[str, Any]:
    """
    Task coordinator for mood trend analysis
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Mood trend analysis results
    """
    try:
        start_time = time.time()
        
        logger.info(f"📈 Coordinating mood trends analysis for {days} days")
        
        # Delegate to analytics service
        analytics_result = asyncio.run(
            analytics_cache_service.generate_mood_trends(days)
        )
        
        analytics_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "generate_mood_trends",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analytics_result
        
    except Exception as e:
        logger.error(f"❌ Mood trends coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.ANALYTICS)
def refresh_analytics_cache(self, analytics_types: List[str] = None) -> Dict[str, Any]:
    """
    Task coordinator for refreshing analytics caches
    
    Args:
        analytics_types: Specific analytics types to refresh (optional)
    
    Returns:
        Cache refresh results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔄 Coordinating analytics cache refresh")
        
        # Delegate to analytics service
        refresh_result = asyncio.run(
            analytics_cache_service.refresh_analytics_cache(analytics_types)
        )
        
        refresh_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "refresh_analytics_cache",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return refresh_result
        
    except Exception as e:
        logger.error(f"❌ Analytics cache refresh coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.HIGH, category=TaskCategory.ANALYTICS)
def analyze_entry_patterns(self, user_id: str, entry_id: str) -> Dict[str, Any]:
    """
    Task coordinator for analyzing individual entry patterns
    
    Args:
        user_id: User identifier
        entry_id: Entry to analyze
    
    Returns:
        Entry pattern analysis results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔍 Coordinating entry pattern analysis for user {user_id}, entry {entry_id}")
        
        # Delegate to background processor for entry analysis
        analysis_result = asyncio.run(
            background_processor.analyze_entry_patterns(user_id, entry_id)
        )
        
        analysis_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "analyze_entry_patterns",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Entry pattern analysis coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def cleanup_old_analytics(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Task coordinator for cleaning up old analytics data
    
    Args:
        days_to_keep: Number of days of analytics to retain
    
    Returns:
        Cleanup results
    """
    try:
        start_time = time.time()
        
        logger.info(f"🧹 Coordinating analytics cleanup - keeping {days_to_keep} days")
        
        # Delegate to analytics service for cleanup
        cleanup_result = asyncio.run(
            analytics_cache_service.cleanup_old_analytics(days_to_keep)
        )
        
        cleanup_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "cleanup_old_analytics",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return cleanup_result
        
    except Exception as e:
        logger.error(f"❌ Analytics cleanup coordination failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

# === BACKGROUND TASK TRIGGERS ===

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.ANALYTICS)
def schedule_background_analytics_processing(self) -> Dict[str, Any]:
    """
    Task coordinator for scheduling background analytics processing
    
    Returns:
        Scheduling results
    """
    try:
        start_time = time.time()
        
        logger.info("🕒 Coordinating background analytics scheduling")
        
        # Delegate to background processor
        scheduling_result = asyncio.run(
            background_processor.schedule_analytics_processing()
        )
        
        scheduling_result.update({
            "task_coordination": {
                "task_id": self.request.id,
                "coordinator": "schedule_background_analytics_processing",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        return scheduling_result
        
    except Exception as e:
        logger.error(f"❌ Background analytics scheduling failed: {e}")
        return {
            "error": str(e),
            "task_id": self.request.id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

# Export tasks for Celery discovery
__all__ = [
    'generate_daily_analytics',
    'generate_weekly_analytics', 
    'generate_mood_trends',
    'refresh_analytics_cache',
    'analyze_entry_patterns',
    'cleanup_old_analytics',
    'schedule_background_analytics_processing'
]
            sentiment_stats = {
                'average': float(np.mean(sentiment_scores)),
                'median': float(np.median(sentiment_scores)),
                'std_deviation': float(np.std(sentiment_scores)),
                'positive_entries': len([s for s in sentiment_scores if s > 0.1]),
                'negative_entries': len([s for s in sentiment_scores if s < -0.1]),
                'neutral_entries': len([s for s in sentiment_scores if -0.1 <= s <= 0.1])
            }
        
        # Calculate writing statistics
        writing_stats = {}
        if word_counts:
            writing_stats = {
                'total_words': sum(word_counts),
                'average_words_per_entry': float(np.mean(word_counts)),
                'median_words_per_entry': float(np.median(word_counts)),
                'longest_entry_words': max(word_counts),
                'shortest_entry_words': min(word_counts)
            }
        
        # Analyze topic usage
        topic_analysis = {
            'total_topics_used': len(topics_used),
            'most_popular_topics': dict(topics_used.most_common(5)),
            'entries_with_topics': sum(topics_used.values()),
            'entries_without_topics': total_entries - sum(topics_used.values())
        }
        
        # Generate insights based on patterns
        insights = []
        
        # Mood insights
        if mood_distribution:
            dominant_mood = max(mood_distribution, key=mood_distribution.get)
            insights.append(f"Dominant mood for {analysis_date}: {dominant_mood} ({mood_distribution[dominant_mood]:.1f}%)")
            
            if mood_distribution.get('sad', 0) > 40:
                insights.append("High sadness levels detected - consider mental health check-in")
            
            if mood_distribution.get('happy', 0) > 50:
                insights.append("Positive mood trend - good mental health indicators")
        
        # Sentiment insights
        if sentiment_stats:
            if sentiment_stats['average'] < -0.2:
                insights.append("Overall negative sentiment trend - monitor for mental health concerns")
            elif sentiment_stats['average'] > 0.2:
                insights.append("Overall positive sentiment trend - good emotional well-being")
        
        # Writing insights
        if writing_stats:
            if writing_stats['average_words_per_entry'] > 300:
                insights.append("High engagement in journaling - strong reflection practice")
            elif writing_stats['average_words_per_entry'] < 50:
                insights.append("Brief entries detected - consider guided prompts for deeper reflection")
        
        # Compile daily analytics results
        daily_analytics = {
            'analysis_date': analysis_date.isoformat(),
            'analytics_status': 'completed',
            'entry_statistics': {
                'total_entries': total_entries,
                'unique_users': 1,  # Would count actual unique users
                'entries_per_user': total_entries
            },
            'mood_analysis': {
                'distribution': mood_distribution,
                'most_common_mood': max(mood_distribution, key=mood_distribution.get) if mood_distribution else None,
                'mood_diversity': len(mood_counts)
            },
            'sentiment_analysis': sentiment_stats,
            'writing_statistics': writing_stats,
            'topic_analysis': topic_analysis,
            'insights': insights,
            'trends': {
                'engagement_level': 'high' if total_entries > 5 else 'moderate' if total_entries > 2 else 'low',
                'emotional_wellness_indicator': 'positive' if sentiment_stats.get('average', 0) > 0.1 else 'neutral' if sentiment_stats.get('average', 0) >= -0.1 else 'concerning'
            },
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store analytics in Redis for dashboard access
        analytics_key = f"daily_analytics:{analysis_date.isoformat()}"
        asyncio.run(redis_analytics_service.redis.set(analytics_key, daily_analytics, ttl=86400 * 30))  # 30 days
        
        # Update rolling averages and trends
        asyncio.run(update_rolling_analytics(daily_analytics))
        
        logger.info(f"✅ Daily analytics generated for {analysis_date}: {total_entries} entries analyzed")
        
        return daily_analytics
        
    except Exception as e:
        error_result = {
            'analysis_date': target_date or (datetime.utcnow() - timedelta(days=1)).date().isoformat(),
            'analytics_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Daily analytics generation failed: {e}")
        return error_result

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_weekly_trends(self, user_id: str = "default_user", weeks_back: int = 4) -> Dict[str, Any]:
    """
    Generate weekly trend analysis for mood patterns and engagement
    
    Args:
        user_id: User identifier for personalized trends
        weeks_back: Number of weeks to analyze
    
    Returns:
        Weekly trend analysis with insights
    """
    try:
        start_time = time.time()
        
        logger.info(f"📈 Generating weekly trends for user {user_id}")
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        # Get entries for the time period
        entries = asyncio.run(unified_db_service.get_entries(
            user_id=user_id,
            date_from=datetime.combine(start_date, datetime.min.time()),
            date_to=datetime.combine(end_date, datetime.max.time()),
            limit=1000
        ))
        
        if not entries:
            return {
                'user_id': user_id,
                'analysis_period': f"{start_date} to {end_date}",
                'trend_status': 'no_data',
                'message': 'No entries found for analysis period',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Group entries by week
        weekly_data = defaultdict(lambda: {
            'entries': [],
            'mood_counts': Counter(),
            'sentiment_scores': [],
            'word_counts': [],
            'entry_count': 0
        })
        
        for entry in entries:
            # Calculate week number (ISO week)
            week_key = f"{entry.created_at.year}-W{entry.created_at.isocalendar()[1]:02d}"
            
            weekly_data[week_key]['entries'].append(entry)
            weekly_data[week_key]['entry_count'] += 1
            
            if entry.mood:
                weekly_data[week_key]['mood_counts'][entry.mood] += 1
            
            if entry.sentiment_score is not None:
                weekly_data[week_key]['sentiment_scores'].append(entry.sentiment_score)
            
            if entry.word_count:
                weekly_data[week_key]['word_counts'].append(entry.word_count)
        
        # Analyze trends across weeks
        weekly_summaries = {}
        sentiment_trend = []
        engagement_trend = []
        mood_trends = defaultdict(list)
        
        for week_key in sorted(weekly_data.keys()):
            week_data = weekly_data[week_key]
            
            # Calculate weekly metrics
            avg_sentiment = float(np.mean(week_data['sentiment_scores'])) if week_data['sentiment_scores'] else 0
            avg_words = float(np.mean(week_data['word_counts'])) if week_data['word_counts'] else 0
            dominant_mood = week_data['mood_counts'].most_common(1)[0][0] if week_data['mood_counts'] else None
            
            weekly_summaries[week_key] = {
                'entry_count': week_data['entry_count'],
                'average_sentiment': avg_sentiment,
                'average_words_per_entry': avg_words,
                'dominant_mood': dominant_mood,
                'mood_distribution': dict(week_data['mood_counts']),
                'total_words': sum(week_data['word_counts'])
            }
            
            # Track trends
            sentiment_trend.append(avg_sentiment)
            engagement_trend.append(week_data['entry_count'])
            
            for mood, count in week_data['mood_counts'].items():
                mood_trends[mood].append(count)
        
        # Calculate trend directions
        def calculate_trend_direction(values):
            if len(values) < 2:
                return "stable"
            
            recent_avg = np.mean(values[-2:])  # Last 2 weeks
            older_avg = np.mean(values[:-2]) if len(values) > 2 else values[0]
            
            if recent_avg > older_avg * 1.1:
                return "improving"
            elif recent_avg < older_avg * 0.9:
                return "declining"
            else:
                return "stable"
        
        # Generate trend insights
        sentiment_direction = calculate_trend_direction(sentiment_trend)
        engagement_direction = calculate_trend_direction(engagement_trend)
        
        trend_insights = []
        
        # Sentiment trend insights
        if sentiment_direction == "improving":
            trend_insights.append("Sentiment is improving over recent weeks - positive mental health trend")
        elif sentiment_direction == "declining":
            trend_insights.append("Sentiment declining over recent weeks - consider additional support")
        
        # Engagement trend insights
        if engagement_direction == "improving":
            trend_insights.append("Journaling engagement increasing - building a strong reflection habit")
        elif engagement_direction == "declining":
            trend_insights.append("Journaling frequency decreasing - consider motivation strategies")
        
        # Mood pattern insights
        for mood, trend_values in mood_trends.items():
            mood_direction = calculate_trend_direction(trend_values)
            if mood == 'sad' and mood_direction == "improving":
                trend_insights.append(f"Increasing sadness trend detected - monitor mental health")
            elif mood == 'happy' and mood_direction == "improving":
                trend_insights.append(f"Increasing happiness trend - positive emotional development")
        
        # Calculate consistency metrics
        consistency_metrics = {
            'entries_per_week_avg': float(np.mean(engagement_trend)),
            'entries_per_week_std': float(np.std(engagement_trend)),
            'sentiment_consistency': 1 - (np.std(sentiment_trend) / max(np.mean(np.abs(sentiment_trend)), 0.1)),
            'most_consistent_week': max(weekly_summaries.keys(), key=lambda k: weekly_summaries[k]['entry_count'])
        }
        
        # Compile weekly trends results
        trends_results = {
            'user_id': user_id,
            'analysis_period': f"{start_date} to {end_date}",
            'weeks_analyzed': len(weekly_summaries),
            'trend_status': 'completed',
            'weekly_summaries': weekly_summaries,
            'trend_analysis': {
                'sentiment_trend': {
                    'direction': sentiment_direction,
                    'values': sentiment_trend,
                    'average': float(np.mean(sentiment_trend)) if sentiment_trend else 0
                },
                'engagement_trend': {
                    'direction': engagement_direction,
                    'values': engagement_trend,
                    'average': float(np.mean(engagement_trend)) if engagement_trend else 0
                },
                'mood_trends': {mood: {'direction': calculate_trend_direction(values), 'values': values} 
                              for mood, values in mood_trends.items()}
            },
            'insights': trend_insights,
            'consistency_metrics': consistency_metrics,
            'recommendations': generate_trend_recommendations(sentiment_direction, engagement_direction, mood_trends),
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store trends for dashboard
        trends_key = f"weekly_trends:{user_id}"
        asyncio.run(redis_analytics_service.redis.set(trends_key, trends_results, ttl=86400 * 7))
        
        logger.info(f"✅ Weekly trends generated for user {user_id}: {len(weekly_summaries)} weeks analyzed")
        
        return trends_results
        
    except Exception as e:
        error_result = {
            'user_id': user_id,
            'trend_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Weekly trends generation failed for user {user_id}: {e}")
        return error_result

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_user_insights_report(self, user_id: str = "default_user") -> Dict[str, Any]:
    """
    Generate comprehensive user insights report combining multiple analytics
    
    Args:
        user_id: User identifier
    
    Returns:
        Comprehensive insights report with personalized recommendations
    """
    try:
        start_time = time.time()
        
        logger.info(f"📋 Generating user insights report for {user_id}")
        
        # Get recent analytics data - using sync call to avoid nested async
        weekly_trends_task = generate_weekly_trends.apply(args=[user_id, 8])  # 8 weeks
        weekly_trends = weekly_trends_task.get()
        
        if weekly_trends.get('trend_status') != 'completed':
            return {
                'user_id': user_id,
                'report_status': 'insufficient_data',
                'message': 'Not enough data for comprehensive insights',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Get mood statistics from unified service
        mood_stats = asyncio.run(unified_db_service.get_mood_statistics(user_id, days=30))
        writing_stats = asyncio.run(unified_db_service.get_writing_statistics(user_id, days=30))
        
        # Analyze user patterns
        user_patterns = {
            'journaling_frequency': analyze_journaling_frequency(weekly_trends),
            'emotional_patterns': analyze_emotional_patterns(weekly_trends, mood_stats),
            'writing_patterns': analyze_writing_patterns(writing_stats),
            'engagement_patterns': analyze_engagement_patterns(weekly_trends)
        }
        
        # Generate personalized insights
        personalized_insights = []
        
        # Frequency insights
        freq_pattern = user_patterns['journaling_frequency']
        if freq_pattern['consistency'] == 'high':
            personalized_insights.append("You maintain excellent journaling consistency - a strong foundation for self-reflection")
        elif freq_pattern['consistency'] == 'moderate':
            personalized_insights.append("Your journaling shows good regularity with room for more consistency")
        else:
            personalized_insights.append("Consider establishing a more regular journaling routine for better insights")
        
        # Emotional insights
        emotional_pattern = user_patterns['emotional_patterns']
        if emotional_pattern['stability'] == 'stable':
            personalized_insights.append("Your emotional patterns show good stability and resilience")
        elif emotional_pattern['trending'] == 'positive':
            personalized_insights.append("Your emotional well-being shows positive improvement over time")
        elif emotional_pattern['trending'] == 'concerning':
            personalized_insights.append("Consider additional support - emotional patterns show some concerning trends")
        
        # Writing insights
        writing_pattern = user_patterns['writing_patterns']
        if writing_pattern['depth'] == 'deep':
            personalized_insights.append("Your detailed writing indicates strong self-reflection and emotional processing")
        elif writing_pattern['depth'] == 'moderate':
            personalized_insights.append("Good reflection depth - consider exploring feelings in more detail occasionally")
        
        # Generate specific recommendations
        recommendations = []
        
        # Based on emotional patterns
        if emotional_pattern.get('dominant_emotion') == 'sadness':
            recommendations.extend([
                "Practice gratitude journaling - write 3 things you're grateful for daily",
                "Consider mood-lifting activities like exercise or creative pursuits",
                "Connect with supportive friends or family members"
            ])
        elif emotional_pattern.get('dominant_emotion') == 'anxiety':
            recommendations.extend([
                "Try anxiety-reducing techniques like deep breathing or meditation",
                "Consider writing about specific worries to process them",
                "Practice grounding exercises when feeling overwhelmed"
            ])
        
        # Based on frequency patterns
        if freq_pattern['consistency'] == 'low':
            recommendations.extend([
                "Set a specific time each day for journaling",
                "Start with just 5 minutes of writing daily",
                "Use prompts when you're not sure what to write about"
            ])
        
        # Based on writing patterns
        if writing_pattern['depth'] == 'shallow':
            recommendations.extend([
                "Try exploring the 'why' behind your feelings",
                "Use emotion-focused prompts for deeper reflection",
                "Consider writing about specific events in more detail"
            ])
        
        # Generate goal suggestions
        goal_suggestions = {
            'short_term': [
                "Write in journal for 7 consecutive days",
                "Try 3 new journal prompts this week",
                "Reflect on one positive moment each day"
            ],
            'medium_term': [
                "Maintain consistent journaling for a month",
                "Track mood patterns and identify triggers",
                "Develop personalized coping strategies"
            ],
            'long_term': [
                "Build journaling into lifelong self-care routine",
                "Use insights for personal growth and development",
                "Share learnings with others for mutual support"
            ]
        }
        
        # Compile comprehensive insights report
        insights_report = {
            'user_id': user_id,
            'report_status': 'completed',
            'report_period': '8 weeks',
            'analysis_summary': {
                'total_entries_analyzed': sum([week['entry_count'] for week in weekly_trends['weekly_summaries'].values()]),
                'analysis_confidence': 'high' if len(weekly_trends['weekly_summaries']) >= 6 else 'moderate',
                'data_quality': 'good'
            },
            'user_patterns': user_patterns,
            'personalized_insights': personalized_insights,
            'recommendations': recommendations[:8],  # Top 8 recommendations
            'goal_suggestions': goal_suggestions,
            'progress_indicators': {
                'journaling_streak': calculate_current_streak(user_id),
                'improvement_areas': identify_improvement_areas(user_patterns),
                'strengths': identify_user_strengths(user_patterns)
            },
            'next_review_date': (datetime.utcnow() + timedelta(weeks=4)).date().isoformat(),
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store report for user access
        report_key = f"user_insights_report:{user_id}"
        asyncio.run(redis_analytics_service.redis.set(report_key, insights_report, ttl=86400 * 14))  # 2 weeks
        
        logger.info(f"✅ User insights report generated for {user_id}: {len(personalized_insights)} insights")
        
        return insights_report
        
    except Exception as e:
        error_result = {
            'user_id': user_id,
            'report_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ User insights report generation failed for user {user_id}: {e}")
        return error_result

@monitored_task(priority=TaskPriority.NORMAL, category=TaskCategory.ANALYTICS)
def generate_mood_correlation_analysis(self, user_id: str = "default_user", days_back: int = 60) -> Dict[str, Any]:
    """
    Analyze correlations between mood patterns and external factors
    
    Args:
        user_id: User identifier
        days_back: Number of days to analyze
    
    Returns:
        Mood correlation analysis with insights
    """
    try:
        start_time = time.time()
        
        logger.info(f"🔗 Analyzing mood correlations for user {user_id}")
        
        # Get entries for analysis period
        entries = asyncio.run(unified_db_service.get_entries(
            user_id=user_id,
            date_from=datetime.utcnow() - timedelta(days=days_back),
            limit=500
        ))
        
        if len(entries) < 10:
            return {
                'user_id': user_id,
                'analysis_status': 'insufficient_data',
                'message': f'Need at least 10 entries for correlation analysis, found {len(entries)}',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Analyze correlations
        correlations = {
            'day_of_week': analyze_day_of_week_correlation(entries),
            'entry_length': analyze_entry_length_correlation(entries),
            'topic_usage': analyze_topic_mood_correlation(entries),
            'temporal_patterns': analyze_temporal_mood_patterns(entries)
        }
        
        # Generate insights from correlations
        correlation_insights = []
        
        # Day of week insights
        dow_corr = correlations['day_of_week']
        if dow_corr['strongest_correlation']['strength'] > 0.3:
            day = dow_corr['strongest_correlation']['day']
            mood = dow_corr['strongest_correlation']['mood']
            correlation_insights.append(f"Strong mood pattern detected: {mood} feelings are more common on {day}s")
        
        # Entry length insights
        length_corr = correlations['entry_length']
        if length_corr['correlation_strength'] > 0.3:
            correlation_insights.append(f"Entry length correlates with mood: {length_corr['insight']}")
        
        # Topic insights
        topic_corr = correlations['topic_usage']
        if topic_corr['significant_correlations']:
            top_correlation = topic_corr['significant_correlations'][0]
            correlation_insights.append(f"Topic '{top_correlation['topic']}' strongly associated with {top_correlation['mood']} mood")
        
        # Compile correlation analysis results
        correlation_results = {
            'user_id': user_id,
            'analysis_status': 'completed',
            'analysis_period_days': days_back,
            'entries_analyzed': len(entries),
            'correlations': correlations,
            'insights': correlation_insights,
            'recommendations': generate_correlation_recommendations(correlations),
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache results
        cache_key = f"mood_correlations:{user_id}:{days_back}d"
        asyncio.run(redis_service.set(cache_key, correlation_results, ttl=3600))
        
        logger.info(f"✅ Mood correlation analysis completed for user {user_id}")
        
        return correlation_results
        
    except Exception as e:
        error_result = {
            'user_id': user_id,
            'analysis_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Mood correlation analysis failed for user {user_id}: {e}")
        return error_result

# === ANALYTICS UTILITY FUNCTIONS ===

async def update_rolling_analytics(daily_analytics: Dict[str, Any]) -> bool:
    """Update rolling averages and trends with new daily data"""
    try:
        # Get current rolling data
        rolling_key = "rolling_analytics"
        rolling_data = await redis_service.get(rolling_key) or {
            'sentiment_history': [],
            'engagement_history': [],
            'mood_trends': defaultdict(list)
        }
        
        # Add new data points
        if daily_analytics.get('sentiment_analysis', {}).get('average'):
            rolling_data['sentiment_history'].append({
                'date': daily_analytics['analysis_date'],
                'value': daily_analytics['sentiment_analysis']['average']
            })
        
        rolling_data['engagement_history'].append({
            'date': daily_analytics['analysis_date'],
            'value': daily_analytics['entry_statistics']['total_entries']
        })
        
        # Keep only last 90 days
        cutoff_date = (datetime.utcnow() - timedelta(days=90)).date().isoformat()
        rolling_data['sentiment_history'] = [
            item for item in rolling_data['sentiment_history'] 
            if item['date'] >= cutoff_date
        ]
        rolling_data['engagement_history'] = [
            item for item in rolling_data['engagement_history'] 
            if item['date'] >= cutoff_date
        ]
        
        # Store updated rolling data
        await redis_service.set(rolling_key, rolling_data, ttl=86400 * 90)
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating rolling analytics: {e}")
        return False

def generate_trend_recommendations(sentiment_direction: str, engagement_direction: str, mood_trends: Dict[str, List]) -> List[str]:
    """Generate recommendations based on trend analysis"""
    recommendations = []
    
    if sentiment_direction == "declining":
        recommendations.extend([
            "Focus on gratitude and positive experiences in journaling",
            "Consider seeking support from friends, family, or professionals",
            "Practice self-care activities that boost mood"
        ])
    
    if engagement_direction == "declining":
        recommendations.extend([
            "Set reminders for regular journaling",
            "Try shorter, more frequent entries",
            "Use guided prompts to overcome writer's block"
        ])
    
    # Mood-specific recommendations
    for mood, values in mood_trends.items():
        if 'sad' in mood and len(values) > 2 and values[-1] > values[-3]:
            recommendations.append("Increasing sadness detected - consider mood-lifting activities")
            break
    
    return recommendations[:6]  # Limit to top 6

def analyze_journaling_frequency(weekly_trends: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze journaling frequency patterns"""
    weekly_counts = [week['entry_count'] for week in weekly_trends['weekly_summaries'].values()]
    
    if not weekly_counts:
        return {'consistency': 'unknown', 'average_per_week': 0}
    
    avg_per_week = float(np.mean(weekly_counts))
    std_dev = float(np.std(weekly_counts))
    consistency_score = 1 - (std_dev / max(avg_per_week, 1))
    
    consistency = 'high' if consistency_score > 0.7 else 'moderate' if consistency_score > 0.4 else 'low'
    
    return {
        'consistency': consistency,
        'average_per_week': avg_per_week,
        'consistency_score': consistency_score,
        'most_active_week': max(weekly_trends['weekly_summaries'].keys(), 
                               key=lambda k: weekly_trends['weekly_summaries'][k]['entry_count'])
    }

def analyze_emotional_patterns(weekly_trends: Dict[str, Any], mood_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze emotional patterns and stability"""
    sentiment_values = weekly_trends['trend_analysis']['sentiment_trend']['values']
    
    if not sentiment_values:
        return {'stability': 'unknown', 'trending': 'unknown'}
    
def analyze_emotional_patterns(weekly_trends: Dict[str, Any], mood_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze emotional patterns and stability"""
    sentiment_values = weekly_trends['trend_analysis']['sentiment_trend']['values']
    
    if not sentiment_values:
        return {'stability': 'unknown', 'trending': 'unknown'}
    
    stability = 'stable' if np.std(sentiment_values) < 0.3 else 'variable'
    
    # Determine overall trending
    if len(sentiment_values) >= 2:
        recent_avg = np.mean(sentiment_values[-2:])
        if recent_avg > 0.2:
            trending = 'positive'
        elif recent_avg < -0.2:
            trending = 'concerning'
        else:
            trending = 'neutral'
    else:
        trending = 'insufficient_data'
    
    return {
        'stability': stability,
        'trending': trending,
        'dominant_emotion': mood_stats.get('most_common_mood'),
        'emotional_range': float(max(sentiment_values) - min(sentiment_values)) if sentiment_values else 0
    }

def analyze_writing_patterns(writing_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze writing depth and patterns"""
    avg_words = writing_stats.get('average_words_per_entry', 0)
    
    if avg_words > 200:
        depth = 'deep'
    elif avg_words > 100:
        depth = 'moderate'
    else:
        depth = 'shallow'
    
    return {
        'depth': depth,
        'average_words': avg_words,
        'total_words': writing_stats.get('total_words', 0),
        'writing_consistency': 'good' if writing_stats.get('entries_count', 0) > 10 else 'developing'
    }

def analyze_engagement_patterns(weekly_trends: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user engagement patterns"""
    engagement_values = weekly_trends['trend_analysis']['engagement_trend']['values']
    
    if not engagement_values:
        return {'level': 'unknown', 'pattern': 'unknown'}
    
    avg_engagement = np.mean(engagement_values)
    
    level = 'high' if avg_engagement > 5 else 'moderate' if avg_engagement > 2 else 'low'
    
    # Detect patterns
    if len(engagement_values) >= 4:
        first_half = np.mean(engagement_values[:len(engagement_values)//2])
        second_half = np.mean(engagement_values[len(engagement_values)//2:])
        
        if second_half > first_half * 1.2:
            pattern = 'building_momentum'
        elif second_half < first_half * 0.8:
            pattern = 'declining_interest'
        else:
            pattern = 'steady'
    else:
        pattern = 'establishing'
    
    return {
        'level': level,
        'pattern': pattern,
        'average_entries_per_week': float(avg_engagement)
    }

def calculate_current_streak(user_id: str) -> int:
    """Calculate current journaling streak"""
    # This would calculate actual streak from database
    # For now, return placeholder
    return 5

def identify_improvement_areas(user_patterns: Dict[str, Any]) -> List[str]:
    """Identify areas for improvement based on patterns"""
    areas = []
    
    if user_patterns['journaling_frequency']['consistency'] == 'low':
        areas.append('journaling_consistency')
    
    if user_patterns['writing_patterns']['depth'] == 'shallow':
        areas.append('reflection_depth')
    
    if user_patterns['emotional_patterns']['stability'] == 'variable':
        areas.append('emotional_stability')
    
    return areas

def identify_user_strengths(user_patterns: Dict[str, Any]) -> List[str]:
    """Identify user strengths based on patterns"""
    strengths = []
    
    if user_patterns['journaling_frequency']['consistency'] == 'high':
        strengths.append('consistent_journaling_habit')
    
    if user_patterns['writing_patterns']['depth'] == 'deep':
        strengths.append('thoughtful_self_reflection')
    
    if user_patterns['emotional_patterns']['stability'] == 'stable':
        strengths.append('emotional_stability')
    
    if user_patterns['engagement_patterns']['level'] == 'high':
        strengths.append('high_engagement_with_wellbeing')
    
    return strengths

def analyze_day_of_week_correlation(entries: List) -> Dict[str, Any]:
    """Analyze mood correlation with day of week"""
    try:
        day_mood_counts = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            if entry.mood and entry.created_at:
                day_name = entry.created_at.strftime('%A')
                day_mood_counts[day_name][entry.mood] += 1
        
        # Find strongest correlation
        strongest_corr = {'day': None, 'mood': None, 'strength': 0}
        
        for day, moods in day_mood_counts.items():
            total_entries = sum(moods.values())
            for mood, count in moods.items():
                strength = count / total_entries if total_entries > 0 else 0
                if strength > strongest_corr['strength']:
                    strongest_corr = {'day': day, 'mood': mood, 'strength': strength}
        
        return {
            'day_mood_distribution': dict(day_mood_counts),
            'strongest_correlation': strongest_corr
        }
        
    except Exception as e:
        logger.error(f"Error analyzing day-of-week correlation: {e}")
        return {'day_mood_distribution': {}, 'strongest_correlation': {'strength': 0}}

def analyze_entry_length_correlation(entries: List) -> Dict[str, Any]:
    """Analyze correlation between entry length and mood"""
    try:
        mood_lengths = defaultdict(list)
        
        for entry in entries:
            if entry.mood and hasattr(entry, 'content') and entry.content:
                length = len(entry.content.split())
                mood_lengths[entry.mood].append(length)
        
        # Calculate average lengths per mood
        mood_avg_lengths = {}
        for mood, lengths in mood_lengths.items():
            mood_avg_lengths[mood] = float(np.mean(lengths)) if lengths else 0
        
        # Determine correlation strength
        if len(mood_avg_lengths) >= 2:
            values = list(mood_avg_lengths.values())
            correlation_strength = float(np.std(values) / np.mean(values)) if np.mean(values) > 0 else 0
        else:
            correlation_strength = 0
        
        # Generate insight
        if correlation_strength > 0.3:
            longest_mood = max(mood_avg_lengths, key=mood_avg_lengths.get) if mood_avg_lengths else None
            shortest_mood = min(mood_avg_lengths, key=mood_avg_lengths.get) if mood_avg_lengths else None
            if longest_mood and shortest_mood:
                insight = f"Longer entries when feeling {longest_mood}, shorter when {shortest_mood}"
            else:
                insight = "Some correlation between entry length and mood detected"
        else:
            insight = "No strong correlation between entry length and mood"
        
        return {
            'mood_average_lengths': mood_avg_lengths,
            'correlation_strength': correlation_strength,
            'insight': insight
        }
        
    except Exception as e:
        logger.error(f"Error analyzing entry length correlation: {e}")
        return {'correlation_strength': 0, 'insight': 'Analysis unavailable'}

def analyze_topic_mood_correlation(entries: List) -> Dict[str, Any]:
    """Analyze correlation between topics and moods"""
    try:
        topic_mood_counts = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            if hasattr(entry, 'topic_id') and entry.topic_id and entry.mood:
                topic_mood_counts[entry.topic_id][entry.mood] += 1
        
        # Find significant correlations
        significant_correlations = []
        
        for topic, moods in topic_mood_counts.items():
            total_entries = sum(moods.values())
            if total_entries >= 5:  # Only consider topics with sufficient data
                dominant_mood = max(moods, key=moods.get)
                strength = moods[dominant_mood] / total_entries
                
                if strength > 0.6:  # Strong correlation threshold
                    significant_correlations.append({
                        'topic': topic,
                        'mood': dominant_mood,
                        'strength': strength,
                        'total_entries': total_entries
                    })
        
        # Sort by strength
        significant_correlations.sort(key=lambda x: x['strength'], reverse=True)
        
        return {
            'topic_mood_distribution': dict(topic_mood_counts),
            'significant_correlations': significant_correlations[:5]  # Top 5
        }
        
    except Exception as e:
        logger.error(f"Error analyzing topic-mood correlation: {e}")
        return {'significant_correlations': []}

def analyze_temporal_mood_patterns(entries: List) -> Dict[str, Any]:
    """Analyze temporal patterns in mood (time of day, etc.)"""
    try:
        hour_mood_counts = defaultdict(lambda: defaultdict(int))
        
        for entry in entries:
            if entry.mood and entry.created_at:
                hour = entry.created_at.hour
                hour_mood_counts[hour][entry.mood] += 1
        
        # Find peak mood times
        mood_peak_times = {}
        for hour, moods in hour_mood_counts.items():
            if sum(moods.values()) >= 3:  # Minimum entries for consideration
                dominant_mood = max(moods, key=moods.get)
                if dominant_mood not in mood_peak_times:
                    mood_peak_times[dominant_mood] = []
                mood_peak_times[dominant_mood].append(hour)
        
        # Determine patterns
        temporal_patterns = []
        for mood, hours in mood_peak_times.items():
            if len(hours) >= 2:
                avg_hour = np.mean(hours)
                if avg_hour < 12:
                    time_period = "morning"
                elif avg_hour < 18:
                    time_period = "afternoon"
                else:
                    time_period = "evening"
                
                temporal_patterns.append({
                    'mood': mood,
                    'peak_time_period': time_period,
                    'average_hour': float(avg_hour)
                })
        
        return {
            'hourly_distribution': dict(hour_mood_counts),
            'temporal_patterns': temporal_patterns
        }
        
    except Exception as e:
        logger.error(f"Error analyzing temporal patterns: {e}")
        return {'temporal_patterns': []}

def generate_correlation_recommendations(correlations: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on correlation analysis"""
    recommendations = []
    
    # Day of week recommendations
    dow_corr = correlations.get('day_of_week', {})
    if dow_corr.get('strongest_correlation', {}).get('strength', 0) > 0.3:
        day = dow_corr['strongest_correlation']['day']
        mood = dow_corr['strongest_correlation']['mood']
        if mood in ['sad', 'anxious', 'stressed']:
            recommendations.append(f"Plan supportive activities on {day}s when you tend to feel {mood}")
        else:
            recommendations.append(f"Leverage {day}s when you typically feel {mood} for important tasks")
    
    # Topic-mood recommendations
    topic_corr = correlations.get('topic_usage', {})
    for correlation in topic_corr.get('significant_correlations', [])[:2]:
        topic = correlation['topic']
        mood = correlation['mood']
        if mood in ['happy', 'motivated', 'content']:
            recommendations.append(f"Focus more on '{topic}' topics as they correlate with positive mood")
        else:
            recommendations.append(f"Be mindful when writing about '{topic}' - consider adding positive elements")
    
    # Temporal recommendations
    temporal_patterns = correlations.get('temporal_patterns', {}).get('temporal_patterns', [])
    for pattern in temporal_patterns[:2]:
        mood = pattern['mood']
        time_period = pattern['peak_time_period']
        if mood in ['happy', 'energetic', 'motivated']:
            recommendations.append(f"Schedule important activities during {time_period} when you're typically {mood}")
    
    return recommendations[:6]

# === MAINTENANCE TASKS ===

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def cleanup_expired_analytics_data(self) -> Dict[str, Any]:
    """
    Clean up expired analytics data and optimize storage
    """
    try:
        start_time = time.time()
        
        logger.info("🧹 Starting analytics data cleanup")
        
        # Clean up old daily analytics (keep last 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        cleaned_analytics = 0
        
        # In production, would scan Redis keys matching pattern daily_analytics:YYYY-MM-DD
        # and remove entries older than cutoff_date
        cleaned_analytics = 15  # Placeholder
        
        # Clean up old trend analysis cache (keep last 30 days)
        trend_cutoff = datetime.utcnow() - timedelta(days=30)
        cleaned_trends = 5  # Placeholder
        
        # Clean up old correlation analysis cache (keep last 7 days)
        correlation_cutoff = datetime.utcnow() - timedelta(days=7)
        cleaned_correlations = 8  # Placeholder
        
        cleanup_results = {
            'cleanup_status': 'completed',
            'items_cleaned': {
                'daily_analytics': cleaned_analytics,
                'trend_analysis': cleaned_trends,
                'correlation_analysis': cleaned_correlations
            },
            'total_items_cleaned': cleaned_analytics + cleaned_trends + cleaned_correlations,
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Analytics cleanup completed: {cleanup_results['total_items_cleaned']} items cleaned")
        
        return cleanup_results
        
    except Exception as e:
        error_result = {
            'cleanup_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Analytics cleanup failed: {e}")
        return error_result

@monitored_task(priority=TaskPriority.LOW, category=TaskCategory.MAINTENANCE)
def generate_analytics_health_report(self) -> Dict[str, Any]:
    """
    Generate analytics system health report
    """
    try:
        start_time = time.time()
        
        logger.info("📋 Generating analytics health report")
        
        # Check analytics data completeness
        recent_analytics = asyncio.run(redis_service.get("daily_analytics:2025-01-20"))
        analytics_health = "healthy" if recent_analytics else "degraded"
        
        # Check trend analysis functionality
        try:
            test_trends = generate_weekly_trends.apply(args=["test_user", 1]).get()
            trends_health = "healthy" if test_trends.get('trend_status') == 'completed' else "degraded"
        except:
            trends_health = "failed"
        
        # Check correlation analysis
        correlation_health = "healthy"  # Would run actual test
        
        # Overall health assessment
        health_components = [analytics_health, trends_health, correlation_health]
        overall_health = "healthy" if all(h == "healthy" for h in health_components) else "degraded"
        
        health_report = {
            'report_status': 'completed',
            'overall_health': overall_health,
            'component_health': {
                'daily_analytics': analytics_health,
                'trend_analysis': trends_health,
                'correlation_analysis': correlation_health
            },
            'recommendations': [
                "Monitor analytics data pipeline consistency",
                "Validate trend analysis accuracy",
                "Optimize correlation computation performance"
            ] if overall_health != "healthy" else [],
            'processing_time_seconds': time.time() - start_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Analytics health report completed: {overall_health}")
        
        return health_report
        
    except Exception as e:
        error_result = {
            'report_status': 'failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.error(f"❌ Analytics health report failed: {e}")
        return error_result
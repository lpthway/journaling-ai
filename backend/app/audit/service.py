# backend/app/audit/service.py
"""
Comprehensive audit service for security event logging.

Features:
- Immutable audit log storage
- User action tracking
- Admin action monitoring with alerts
- AI processing event logging
- Security event correlation
- Compliance reporting
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from fastapi import Request

from .database import audit_database
from .models import (
    AuditEvent, EventType, ActionType,
    UserAction, AdminAction, AIProcessingEvent, SecurityEvent
)
from ..core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class AuditService:
    """
    Comprehensive audit service for security and compliance logging.
    
    Design principles:
    - Immutable audit logs (write-only)
    - Security event correlation
    - Real-time threat detection
    - Compliance reporting
    - Performance monitoring
    """
    
    def __init__(self):
        self._initialized = False
        self._event_cache = []
        self._cache_size_limit = 100
        
        # Security alert thresholds
        self._alert_thresholds = {
            "failed_logins_per_hour": 5,
            "admin_actions_per_hour": 20,
            "bulk_data_access_threshold": 50
        }
    
    async def initialize(self) -> None:
        """Initialize audit service."""
        try:
            await audit_database.initialize()
            self._initialized = True
            logger.info("✅ Audit service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Audit service initialization failed: {e}")
            raise
    
    async def log_user_action(
        self,
        user_id: str,
        action: ActionType,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        description: Optional[str] = None
    ) -> None:
        """
        Log user action with comprehensive context.
        
        Args:
            user_id: User identifier
            action: Type of action performed
            resource_type: Type of resource accessed (entry, topic, session)
            resource_id: Specific resource identifier
            success: Whether action was successful
            metadata: Additional context data
            request: FastAPI request object for context
            description: Human-readable description
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract request context
            ip_address = None
            user_agent = None
            request_id = None
            
            if request:
                ip_address = self._extract_client_ip(request)
                user_agent = request.headers.get("user-agent")
                request_id = getattr(request.state, "correlation_id", None)
            
            # Build audit event
            audit_event = AuditEvent(
                event_type=EventType.USER_ACTION,
                action_type=action,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description or f"User {action.value} on {resource_type or 'system'}",
                success=success,
                risk_level=self._calculate_risk_level(action, success),
                event_metadata=metadata or {},
                contains_pii=self._action_contains_pii(action),
                data_classification="user_data"
            )
            
            # Store audit event
            await self._store_audit_event(audit_event)
            
            # Check for security alerts
            await self._check_security_alerts(audit_event)
            
            logger.debug(f"User action logged: {user_id} - {action.value}")
            
        except Exception as e:
            logger.error(f"Failed to log user action: {e}")
            # Don't raise exception - audit logging should not break application
    
    async def log_admin_action(
        self,
        admin_user_id: str,
        action: ActionType,
        target_user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> None:
        """
        Log admin action with enhanced monitoring.
        
        Args:
            admin_user_id: Admin user identifier
            action: Type of admin action
            target_user_id: User being affected by admin action
            resource_type: Type of resource accessed
            resource_id: Specific resource identifier
            reason: Reason for admin action
            metadata: Additional context data
            request: FastAPI request object
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract request context
            ip_address = None
            user_agent = None
            request_id = None
            
            if request:
                ip_address = self._extract_client_ip(request)
                user_agent = request.headers.get("user-agent")
                request_id = getattr(request.state, "correlation_id", None)
            
            # Build audit event with admin-specific fields
            audit_event = AuditEvent(
                event_type=EventType.ADMIN_ACTION,
                action_type=action,
                admin_user_id=admin_user_id,
                user_id=target_user_id,  # User being affected
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                resource_type=resource_type,
                resource_id=resource_id,
                description=f"Admin {action.value}: {reason or 'No reason provided'}",
                success=True,  # We'll log separately if admin action fails
                risk_level="high",  # Admin actions are always high risk
                event_metadata={
                    "reason": reason,
                    "admin_justification": reason,
                    **(metadata or {})
                },
                contains_pii=True,  # Admin actions often involve PII
                data_classification="admin_access",
                compliance_tags={
                    "requires_review": True,
                    "admin_override": True,
                    "audit_priority": "high"
                }
            )
            
            # Store audit event
            await self._store_audit_event(audit_event)
            
            # Admin actions trigger immediate alerts
            await self._alert_admin_action(audit_event)
            
            logger.warning(
                f"ADMIN ACTION: {admin_user_id} performed {action.value} on user {target_user_id}",
                extra={
                    "admin_user_id": admin_user_id,
                    "target_user_id": target_user_id,
                    "action": action.value,
                    "reason": reason,
                    "security_event": "admin_action"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
    
    async def log_ai_processing(
        self,
        user_id: str,
        session_id: str,
        operation: str,
        data_types: List[str],
        consent_given: bool,
        processing_time_ms: Optional[int] = None,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log AI processing events for transparency.
        
        Args:
            user_id: User whose data is being processed
            session_id: AI processing session identifier
            operation: Type of AI operation (analysis, sentiment, etc.)
            data_types: Types of data being processed
            consent_given: Whether user gave explicit consent
            processing_time_ms: Processing duration
            model_used: AI model identifier
            metadata: Additional processing details
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            audit_event = AuditEvent(
                event_type=EventType.AI_PROCESSING,
                action_type=ActionType.AI_ANALYSIS_START if operation == "start" else ActionType.AI_ANALYSIS_COMPLETE,
                user_id=user_id,
                session_id=session_id,
                resource_type="ai_processing",
                resource_id=session_id,
                description=f"AI {operation} for user {user_id}: {', '.join(data_types)}",
                success=True,
                risk_level="medium" if consent_given else "high",
                event_metadata={
                    "operation": operation,
                    "data_types": data_types,
                    "consent_given": consent_given,
                    "model_used": model_used,
                    "processing_time_ms": processing_time_ms,
                    **(metadata or {})
                },
                contains_pii=True,  # AI processing involves user content
                data_classification="ai_processing",
                compliance_tags={
                    "ai_processing": True,
                    "consent_required": True,
                    "user_consent_given": consent_given
                },
                response_time_ms=processing_time_ms
            )
            
            await self._store_audit_event(audit_event)
            
            logger.info(
                f"AI processing logged: {operation} for user {user_id}",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "operation": operation,
                    "consent_given": consent_given,
                    "data_types": data_types
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to log AI processing: {e}")
    
    async def log_security_event(
        self,
        event_type: ActionType,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        risk_level: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> None:
        """
        Log security events for threat detection.
        
        Args:
            event_type: Type of security event
            description: Event description
            user_id: User involved (if any)
            ip_address: Source IP address
            risk_level: Risk assessment (low, medium, high, critical)
            metadata: Additional event data
            request: FastAPI request object
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Extract additional context from request
            if request and not ip_address:
                ip_address = self._extract_client_ip(request)
            
            audit_event = AuditEvent(
                event_type=EventType.SECURITY_EVENT,
                action_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=request.headers.get("user-agent") if request else None,
                description=description,
                success=False,  # Security events are typically failures
                risk_level=risk_level,
                event_metadata=metadata or {},
                contains_pii=user_id is not None,
                data_classification="security_event",
                compliance_tags={
                    "security_incident": True,
                    "requires_investigation": risk_level in ["high", "critical"]
                }
            )
            
            await self._store_audit_event(audit_event)
            
            # Security events may trigger alerts
            if risk_level in ["high", "critical"]:
                await self._alert_security_event(audit_event)
            
            logger.warning(
                f"SECURITY EVENT: {event_type.value} - {description}",
                extra={
                    "security_event": event_type.value,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "risk_level": risk_level
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def get_audit_events(
        self,
        user_id: Optional[str] = None,
        admin_user_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """
        Retrieve audit events for reporting and investigation.
        
        Args:
            user_id: Filter by user
            admin_user_id: Filter by admin user
            event_type: Filter by event type
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List[AuditEvent]: Matching audit events
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with audit_database.get_session() as session:
                query = select(AuditEvent).order_by(AuditEvent.timestamp.desc())
                
                # Apply filters
                if user_id:
                    query = query.where(AuditEvent.user_id == user_id)
                if admin_user_id:
                    query = query.where(AuditEvent.admin_user_id == admin_user_id)
                if event_type:
                    query = query.where(AuditEvent.event_type == event_type)
                if start_time:
                    query = query.where(AuditEvent.timestamp >= start_time)
                if end_time:
                    query = query.where(AuditEvent.timestamp <= end_time)
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to retrieve audit events: {e}")
            raise DatabaseException(f"Audit query failed: {e}")
    
    def _extract_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else None
    
    def _calculate_risk_level(self, action: ActionType, success: bool) -> str:
        """Calculate risk level based on action type and outcome."""
        if not success:
            return "high"  # Failed actions are always high risk
        
        high_risk_actions = {
            ActionType.DELETE_ACCOUNT,
            ActionType.EXPORT_DATA,
            ActionType.DELETE_ENTRY
        }
        
        medium_risk_actions = {
            ActionType.CREATE_ENTRY,
            ActionType.UPDATE_ENTRY,
            ActionType.AI_ANALYSIS_START
        }
        
        if action in high_risk_actions:
            return "high"
        elif action in medium_risk_actions:
            return "medium"
        else:
            return "low"
    
    def _action_contains_pii(self, action: ActionType) -> bool:
        """Determine if action involves PII."""
        pii_actions = {
            ActionType.CREATE_ENTRY,
            ActionType.UPDATE_ENTRY,
            ActionType.VIEW_ENTRY,
            ActionType.EXPORT_DATA,
            ActionType.AI_ANALYSIS_START
        }
        return action in pii_actions
    
    async def _store_audit_event(self, audit_event: AuditEvent) -> None:
        """Store audit event in database."""
        try:
            async with audit_database.get_session() as session:
                session.add(audit_event)
                await session.flush()  # Immediate write for audit
                
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            # Store in cache for retry
            if len(self._event_cache) < self._cache_size_limit:
                self._event_cache.append(audit_event)
            raise
    
    async def _check_security_alerts(self, audit_event: AuditEvent) -> None:
        """Check if event triggers security alerts."""
        try:
            # Check for failed login patterns
            if audit_event.action_type == ActionType.LOGIN and not audit_event.success:
                await self._check_failed_login_pattern(audit_event)
            
            # Check for suspicious activity patterns
            if audit_event.risk_level == "high":
                await self._check_suspicious_activity(audit_event)
                
        except Exception as e:
            logger.error(f"Security alert check failed: {e}")
    
    async def _check_failed_login_pattern(self, audit_event: AuditEvent) -> None:
        """Check for suspicious failed login patterns."""
        # This would implement real-time threat detection
        # For now, just log pattern detection
        logger.warning(f"Failed login detected for user {audit_event.user_id}")
    
    async def _check_suspicious_activity(self, audit_event: AuditEvent) -> None:
        """Check for suspicious activity patterns."""
        # This would implement behavioral analysis
        logger.info(f"High-risk activity detected: {audit_event.action_type}")
    
    async def _alert_admin_action(self, audit_event: AuditEvent) -> None:
        """Alert on admin actions."""
        # This would integrate with alerting systems
        logger.warning(f"ADMIN ALERT: {audit_event.description}")
    
    async def _alert_security_event(self, audit_event: AuditEvent) -> None:
        """Alert on security events."""
        # This would integrate with security incident response
        logger.error(f"SECURITY ALERT: {audit_event.description}")


# Global audit service instance
audit_service = AuditService()
# backend/app/core/request_tracing.py
"""
Request Tracing and Observability Middleware
Provides distributed tracing, request ID generation, and performance tracking
"""

import time
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.performance_monitor import performance_monitor

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)

logger = logging.getLogger(__name__)

@dataclass
class RequestTrace:
    """Request trace information"""
    request_id: str
    method: str
    path: str
    user_agent: Optional[str]
    ip_address: str
    user_id: Optional[str]
    session_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None
    error: Optional[str] = None

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing and performance monitoring"""
    
    def __init__(self, app: ASGIApp, enable_detailed_logging: bool = True):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        self.traces: Dict[str, RequestTrace] = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing and monitoring"""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Extract user context from headers or auth
        user_id = request.headers.get("X-User-ID")
        session_id = request.headers.get("X-Session-ID")
        
        if user_id:
            user_id_var.set(user_id)
        if session_id:
            session_id_var.set(session_id)
        
        # Create trace record
        trace = RequestTrace(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("User-Agent"),
            ip_address=self._get_client_ip(request),
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.utcnow()
        )
        
        # Store trace
        self.traces[request_id] = trace
        
        # Add request ID to response headers
        start_time = time.time()
        
        try:
            # Use performance monitor for timing
            async with performance_monitor.timed_operation(
                f"request_{request.method}_{request.url.path}",
                tags={
                    "method": request.method,
                    "path": request.url.path,
                    "user_id": user_id or "anonymous",
                    "request_id": request_id
                }
            ):
                response = await call_next(request)
            
            # Record successful completion
            trace.end_time = datetime.utcnow()
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.status_code = response.status_code
            trace.response_size = int(response.headers.get("content-length", 0))
            
            # Add tracing headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{trace.duration_ms:.2f}ms"
            
            # Log request completion
            if self.enable_detailed_logging:
                self._log_request_completion(trace)
            
            return response
            
        except Exception as e:
            # Record error
            trace.end_time = datetime.utcnow()
            trace.duration_ms = (time.time() - start_time) * 1000
            trace.error = str(e)
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "duration_ms": trace.duration_ms,
                    "error": str(e)
                }
            )
            
            raise
        
        finally:
            # Clean up old traces (keep last 1000)
            if len(self.traces) > 1000:
                oldest_keys = list(self.traces.keys())[:100]
                for key in oldest_keys:
                    del self.traces[key]
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _log_request_completion(self, trace: RequestTrace) -> None:
        """Log request completion with structured data"""
        log_level = logging.INFO
        
        # Use WARNING for slow requests (>1s) or ERROR for failures
        if trace.duration_ms and trace.duration_ms > 1000:
            log_level = logging.WARNING
        
        if trace.status_code and trace.status_code >= 400:
            log_level = logging.ERROR if trace.status_code >= 500 else logging.WARNING
        
        logger.log(
            log_level,
            f"{trace.method} {trace.path} - {trace.status_code} - {trace.duration_ms:.2f}ms",
            extra={
                "request_id": trace.request_id,
                "method": trace.method,
                "path": trace.path,
                "status_code": trace.status_code,
                "duration_ms": trace.duration_ms,
                "user_id": trace.user_id,
                "session_id": trace.session_id,
                "ip_address": trace.ip_address,
                "user_agent": trace.user_agent,
                "response_size": trace.response_size,
                "error": trace.error
            }
        )
    
    def get_active_traces(self) -> Dict[str, RequestTrace]:
        """Get currently active traces"""
        return self.traces.copy()
    
    def get_trace_by_id(self, request_id: str) -> Optional[RequestTrace]:
        """Get specific trace by request ID"""
        return self.traces.get(request_id)

# Context helper functions
def get_current_request_id() -> Optional[str]:
    """Get current request ID from context"""
    return request_id_var.get()

def get_current_user_id() -> Optional[str]:
    """Get current user ID from context"""
    return user_id_var.get()

def get_current_session_id() -> Optional[str]:
    """Get current session ID from context"""
    return session_id_var.get()

def get_contextual_logger(name: str) -> logging.LoggerAdapter:
    """Get logger with current request context"""
    logger = logging.getLogger(name)
    
    extra = {}
    if request_id := get_current_request_id():
        extra["request_id"] = request_id
    if user_id := get_current_user_id():
        extra["user_id"] = user_id
    if session_id := get_current_session_id():
        extra["session_id"] = session_id
    
    return logging.LoggerAdapter(logger, extra)

class TraceMetrics:
    """Collect tracing metrics for monitoring"""
    
    def __init__(self):
        self.request_counts = {}
        self.response_times = []
        self.error_counts = {}
        self.status_codes = {}
    
    def record_request(self, trace: RequestTrace) -> None:
        """Record request metrics"""
        # Count requests by path
        path_key = f"{trace.method} {trace.path}"
        self.request_counts[path_key] = self.request_counts.get(path_key, 0) + 1
        
        # Record response time
        if trace.duration_ms:
            self.response_times.append(trace.duration_ms)
            # Keep only recent times (last 1000)
            if len(self.response_times) > 1000:
                self.response_times = self.response_times[-1000:]
        
        # Count status codes
        if trace.status_code:
            self.status_codes[trace.status_code] = self.status_codes.get(trace.status_code, 0) + 1
        
        # Count errors
        if trace.error:
            error_type = type(trace.error).__name__ if hasattr(trace.error, '__class__') else "unknown"
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tracing metrics summary"""
        total_requests = sum(self.request_counts.values())
        error_count = sum(count for status, count in self.status_codes.items() if status >= 400)
        
        response_times_sorted = sorted(self.response_times) if self.response_times else [0]
        
        return {
            "total_requests": total_requests,
            "error_rate": error_count / max(total_requests, 1),
            "avg_response_time_ms": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "p50_response_time_ms": response_times_sorted[len(response_times_sorted)//2],
            "p95_response_time_ms": response_times_sorted[int(len(response_times_sorted)*0.95)] if len(response_times_sorted) > 20 else 0,
            "top_endpoints": dict(sorted(self.request_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "status_code_distribution": self.status_codes.copy(),
            "error_types": self.error_counts.copy()
        }

# Global tracing metrics instance
trace_metrics = TraceMetrics()

# Global middleware instance for access to traces
request_tracer: Optional[RequestTracingMiddleware] = None

def get_request_tracer() -> Optional[RequestTracingMiddleware]:
    """Get the global request tracer instance"""
    return request_tracer

def set_request_tracer(tracer: RequestTracingMiddleware) -> None:
    """Set the global request tracer instance"""
    global request_tracer
    request_tracer = tracer
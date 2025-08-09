# backend/app/core/security_middleware.py
"""
Security middleware for adding security headers and protection.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from typing import Callable
import uuid


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    def __init__(self, app, nonce_generator: bool = True):
        super().__init__(app)
        self.nonce_generator = nonce_generator
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        
        response = await call_next(request)
        
        # Generate CSP nonce for dynamic content
        nonce = str(uuid.uuid4()) if self.nonce_generator else None
        
        # Content Security Policy - strict but functional
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-eval'" + (f" 'nonce-{nonce}'" if nonce else ""),
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com",
            "font-src 'self' fonts.gstatic.com",
            "img-src 'self' data: blob:",
            "media-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "connect-src 'self' http://localhost:8000 ws://localhost:*"
        ]
        
        security_headers = {
            # Content Security Policy
            "Content-Security-Policy": "; ".join(csp_directives),
            
            # Clickjacking protection
            "X-Frame-Options": "DENY",
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Content type sniffing protection
            "X-Content-Type-Options": "nosniff",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy (formerly Feature-Policy)
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            
            # HSTS (HTTP Strict Transport Security) - only for HTTPS
            # Note: Only enable in production with HTTPS
            # "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Server information hiding
            "Server": "FastAPI",
            
            # Cache control for sensitive endpoints
            "Cache-Control": "no-cache, no-store, must-revalidate" if request.url.path.startswith("/api/v1/auth") else "public, max-age=300"
        }
        
        # Add security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Add nonce to request state if generated
        if nonce:
            request.state.csp_nonce = nonce
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security-focused request logging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests for security monitoring."""
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log security-relevant requests
        sensitive_paths = ["/auth/", "/admin/", "/api/v1/auth/"]
        is_sensitive = any(path in str(request.url) for path in sensitive_paths)
        
        if is_sensitive:
            # This would typically go to a security log
            import logging
            security_logger = logging.getLogger("security")
            security_logger.info(
                f"Request {request_id}: {request.method} {request.url} "
                f"from {client_ip} ({user_agent[:100]})"
            )
        
        try:
            response = await call_next(request)
            
            # Log failed authentication attempts
            if (is_sensitive and 
                response.status_code in [401, 403, 429]):
                security_logger.warning(
                    f"Security event {request_id}: Status {response.status_code} "
                    f"for {request.method} {request.url} from {client_ip}"
                )
            
            return response
            
        except Exception as e:
            # Log exceptions in sensitive endpoints
            if is_sensitive:
                security_logger.error(
                    f"Exception in {request_id}: {str(e)} "
                    f"for {request.method} {request.url} from {client_ip}"
                )
            raise


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware for API protection.
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}  # In production, use Redis or similar
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        
        # Simple sliding window rate limiting
        import time
        current_time = int(time.time() / 60)  # Current minute
        
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = {}
        
        # Clean old entries (keep last 2 minutes)
        old_minutes = [m for m in self.client_requests[client_ip] if m < current_time - 2]
        for old_minute in old_minutes:
            del self.client_requests[client_ip][old_minute]
        
        # Count requests in current minute
        current_requests = self.client_requests[client_ip].get(current_time, 0)
        
        if current_requests >= self.requests_per_minute:
            # Rate limit exceeded
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Increment counter
        self.client_requests[client_ip][current_time] = current_requests + 1
        
        return await call_next(request)
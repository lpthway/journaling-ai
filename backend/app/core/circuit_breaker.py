# backend/app/core/circuit_breaker.py
"""
Circuit Breaker Pattern Implementation for External Service Calls

Provides resilient handling of external service calls by:
- Tracking failures and automatically opening the circuit when threshold is reached
- Allowing recovery attempts through half-open state
- Preventing cascading failures and resource exhaustion
- Monitoring and alerting for service health
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, Dict, List, Union
from dataclasses import dataclass, field
from functools import wraps
import threading

from app.core.config import settings

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation, calls pass through
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5           # Number of failures to trigger opening
    recovery_timeout: int = 60          # Seconds before allowing recovery attempt  
    success_threshold: int = 3          # Successes needed in half-open to close
    timeout: float = 30.0               # Request timeout in seconds
    expected_exceptions: tuple = (Exception,)  # Exception types that count as failures
    
    # Monitoring and alerting
    monitor_window: int = 300           # Window for calculating failure rates (seconds)
    alert_threshold: float = 0.5        # Alert when failure rate exceeds this
    max_concurrent_calls: int = 10      # Limit concurrent calls to prevent resource exhaustion


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics and metrics"""
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_timeouts: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    failure_rate: float = 0.0
    avg_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors"""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Raised when circuit breaker is open"""
    def __init__(self, service_name: str, last_failure: Optional[str] = None):
        self.service_name = service_name
        self.last_failure = last_failure
        message = f"Circuit breaker OPEN for service '{service_name}'"
        if last_failure:
            message += f". Last failure: {last_failure}"
        super().__init__(message)


class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Raised when circuit breaker times out"""
    def __init__(self, service_name: str, timeout: float):
        self.service_name = service_name
        self.timeout = timeout
        super().__init__(f"Circuit breaker timeout ({timeout}s) for service '{service_name}'")


class CircuitBreaker:
    """
    Circuit Breaker implementation for external service calls.
    
    Provides automatic failure detection and recovery for external dependencies.
    """
    
    def __init__(self, service_name: str, config: Optional[CircuitBreakerConfig] = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._active_calls = 0
        self._state_changed_at = datetime.now()
        self._last_alert_time: Optional[datetime] = None
        
        logger.info(f"Circuit breaker initialized for service '{service_name}' with config: "
                   f"failure_threshold={self.config.failure_threshold}, "
                   f"recovery_timeout={self.config.recovery_timeout}s")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for applying circuit breaker to functions"""
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self.call(func, *args, **kwargs)
            return sync_wrapper
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        with self._lock:
            self._check_concurrent_limit()
            
            if self.state == CircuitBreakerState.OPEN:
                if not self._should_attempt_reset():
                    self._record_failure("Circuit breaker is OPEN")
                    raise CircuitBreakerOpenError(self.service_name, self._get_last_failure())
                else:
                    self._transition_to_half_open()
            
            self._active_calls += 1
            self.stats.total_calls += 1
        
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            response_time = time.time() - start_time
            self._record_success(response_time)
            return result
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self._record_timeout(response_time)
            raise CircuitBreakerTimeoutError(self.service_name, self.config.timeout)
            
        except self.config.expected_exceptions as e:
            response_time = time.time() - start_time
            self._record_failure(str(e), response_time)
            raise
            
        finally:
            with self._lock:
                self._active_calls -= 1
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute sync function with circuit breaker protection"""
        with self._lock:
            self._check_concurrent_limit()
            
            if self.state == CircuitBreakerState.OPEN:
                if not self._should_attempt_reset():
                    self._record_failure("Circuit breaker is OPEN")
                    raise CircuitBreakerOpenError(self.service_name, self._get_last_failure())
                else:
                    self._transition_to_half_open()
            
            self._active_calls += 1
            self.stats.total_calls += 1
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            response_time = time.time() - start_time
            self._record_success(response_time)
            return result
            
        except self.config.expected_exceptions as e:
            response_time = time.time() - start_time
            self._record_failure(str(e), response_time)
            raise
            
        finally:
            with self._lock:
                self._active_calls -= 1
    
    def _check_concurrent_limit(self):
        """Check if concurrent call limit is exceeded"""
        if self._active_calls >= self.config.max_concurrent_calls:
            raise CircuitBreakerError(f"Too many concurrent calls to service '{self.service_name}' "
                                    f"({self._active_calls}/{self.config.max_concurrent_calls})")
    
    def _record_success(self, response_time: float):
        """Record a successful call"""
        with self._lock:
            self.stats.total_successes += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = datetime.now()
            
            # Track response times
            self.stats.response_times.append(response_time)
            if len(self.stats.response_times) > 100:  # Keep last 100 response times
                self.stats.response_times = self.stats.response_times[-100:]
            
            self._update_avg_response_time()
            self._update_failure_rate()
            
            # State transition logic
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()
            
            logger.debug(f"Circuit breaker success for '{self.service_name}' "
                        f"(response_time={response_time:.3f}s, consecutive={self.stats.consecutive_successes})")
    
    def _record_failure(self, error_message: str, response_time: Optional[float] = None):
        """Record a failed call"""
        with self._lock:
            self.stats.total_failures += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = datetime.now()
            
            if response_time is not None:
                self.stats.response_times.append(response_time)
                self._update_avg_response_time()
            
            self._update_failure_rate()
            
            # State transition logic
            if (self.state in [CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN] and
                self.stats.consecutive_failures >= self.config.failure_threshold):
                self._transition_to_open()
            
            # Check if alert should be sent
            self._check_alert_conditions()
            
            logger.warning(f"Circuit breaker failure for '{self.service_name}': {error_message} "
                          f"(consecutive={self.stats.consecutive_failures}, state={self.state.value})")
    
    def _record_timeout(self, response_time: float):
        """Record a timeout (treated as failure)"""
        with self._lock:
            self.stats.total_timeouts += 1
            self._record_failure(f"Timeout after {self.config.timeout}s", response_time)
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.state != CircuitBreakerState.OPEN:
            return False
        
        time_since_open = (datetime.now() - self._state_changed_at).total_seconds()
        return time_since_open >= self.config.recovery_timeout
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self._state_changed_at = datetime.now()
        self._record_state_change(old_state, self.state)
        logger.info(f"Circuit breaker for '{self.service_name}' transitioned to CLOSED")
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self._state_changed_at = datetime.now()
        self._record_state_change(old_state, self.state)
        logger.error(f"Circuit breaker for '{self.service_name}' transitioned to OPEN "
                    f"(consecutive_failures={self.stats.consecutive_failures})")
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self._state_changed_at = datetime.now()
        self._record_state_change(old_state, self.state)
        logger.info(f"Circuit breaker for '{self.service_name}' transitioned to HALF_OPEN (attempting recovery)")
    
    def _record_state_change(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState):
        """Record state change for monitoring"""
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "from_state": old_state.value,
            "to_state": new_state.value,
            "consecutive_failures": self.stats.consecutive_failures,
            "total_failures": self.stats.total_failures,
            "total_calls": self.stats.total_calls
        }
        self.stats.state_changes.append(change_record)
        
        # Keep only last 50 state changes
        if len(self.stats.state_changes) > 50:
            self.stats.state_changes = self.stats.state_changes[-50:]
    
    def _update_failure_rate(self):
        """Update failure rate based on recent calls"""
        if self.stats.total_calls == 0:
            self.stats.failure_rate = 0.0
        else:
            self.stats.failure_rate = self.stats.total_failures / self.stats.total_calls
    
    def _update_avg_response_time(self):
        """Update average response time"""
        if self.stats.response_times:
            self.stats.avg_response_time = sum(self.stats.response_times) / len(self.stats.response_times)
    
    def _check_alert_conditions(self):
        """Check if alert conditions are met"""
        if (self.stats.failure_rate >= self.config.alert_threshold and
            (not self._last_alert_time or 
             (datetime.now() - self._last_alert_time).total_seconds() > 300)):  # Alert once every 5 minutes
            
            self._send_alert()
            self._last_alert_time = datetime.now()
    
    def _send_alert(self):
        """Send alert about high failure rate (placeholder for actual alerting)"""
        logger.critical(f"ALERT: Circuit breaker '{self.service_name}' has high failure rate "
                       f"({self.stats.failure_rate:.1%}) - state: {self.state.value}")
        # TODO: Implement actual alerting (email, webhook, monitoring system, etc.)
    
    def _get_last_failure(self) -> Optional[str]:
        """Get description of last failure"""
        if self.stats.last_failure_time:
            return f"Last failure at {self.stats.last_failure_time.strftime('%Y-%m-%d %H:%M:%S')}"
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self._lock:
            return {
                "service_name": self.service_name,
                "state": self.state.value,
                "state_changed_at": self._state_changed_at.isoformat(),
                "total_calls": self.stats.total_calls,
                "total_successes": self.stats.total_successes,
                "total_failures": self.stats.total_failures,
                "total_timeouts": self.stats.total_timeouts,
                "consecutive_failures": self.stats.consecutive_failures,
                "consecutive_successes": self.stats.consecutive_successes,
                "failure_rate": round(self.stats.failure_rate, 4),
                "avg_response_time": round(self.stats.avg_response_time, 3),
                "active_calls": self._active_calls,
                "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout,
                    "max_concurrent_calls": self.config.max_concurrent_calls
                },
                "recent_state_changes": self.stats.state_changes[-10:]  # Last 10 changes
            }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        with self._lock:
            old_state = self.state
            self.state = CircuitBreakerState.CLOSED
            self._state_changed_at = datetime.now()
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            self._record_state_change(old_state, self.state)
            logger.info(f"Circuit breaker for '{self.service_name}' manually reset to CLOSED")
    
    def force_open(self):
        """Manually force circuit breaker to open state"""
        with self._lock:
            old_state = self.state
            self.state = CircuitBreakerState.OPEN
            self._state_changed_at = datetime.now()
            self._record_state_change(old_state, self.state)
            logger.warning(f"Circuit breaker for '{self.service_name}' manually forced to OPEN")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_breaker(self, service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker for a service"""
        with self._lock:
            if service_name not in self._breakers:
                self._breakers[service_name] = CircuitBreaker(service_name, config)
            return self._breakers[service_name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        with self._lock:
            return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
    
    def get_unhealthy_services(self) -> List[str]:
        """Get list of services with unhealthy circuit breakers"""
        with self._lock:
            unhealthy = []
            for name, breaker in self._breakers.items():
                if (breaker.state == CircuitBreakerState.OPEN or 
                    breaker.stats.failure_rate > breaker.config.alert_threshold):
                    unhealthy.append(name)
            return unhealthy


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()


# Convenience functions for common patterns
def circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator factory for applying circuit breaker to functions"""
    return circuit_breaker_registry.get_breaker(service_name, config)


def get_service_circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get circuit breaker for a specific service"""
    return circuit_breaker_registry.get_breaker(service_name, config)
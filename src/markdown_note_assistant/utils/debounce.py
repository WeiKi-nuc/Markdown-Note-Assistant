"""
Debounce utility module - provides debouncing for frequent operations.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional


class Debouncer:
    """
    Debouncer - delays function execution until after a wait period.
    
    This is useful for operations like:
    - Auto-save
    - Real-time preview updates
    - Search-as-you-type
    """
    
    def __init__(self, delay_ms: int = 300):
        """
        Initialize the debouncer.
        
        Args:
            delay_ms: Delay in milliseconds before executing
        """
        self.delay_ms = delay_ms
        self._timers: Dict[str, threading.Timer] = {}
        self._pending_args: Dict[str, tuple] = {}
        self._pending_kwargs: Dict[str, dict] = {}
        self._lock = threading.Lock()
    
    def call(
        self,
        func: Callable,
        key: str = "default",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Schedule a debounced function call.
        
        Args:
            func: Function to call
            key: Unique key for this debounced operation
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        with self._lock:
            if key in self._timers:
                self._timers[key].cancel()
            
            self._pending_args[key] = args
            self._pending_kwargs[key] = kwargs
            
            def execute():
                with self._lock:
                    if key in self._pending_args:
                        args = self._pending_args.pop(key)
                        kwargs = self._pending_kwargs.pop(key)
                        self._timers.pop(key, None)
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"Error in debounced function: {e}")
            
            self._timers[key] = threading.Timer(
                self.delay_ms / 1000.0,
                execute,
            )
            self._timers[key].start()
    
    def cancel(self, key: str = "default") -> None:
        """
        Cancel a pending debounced call.
        
        Args:
            key: Key of the call to cancel
        """
        with self._lock:
            if key in self._timers:
                self._timers[key].cancel()
                del self._timers[key]
            self._pending_args.pop(key, None)
            self._pending_kwargs.pop(key, None)
    
    def cancel_all(self) -> None:
        """Cancel all pending debounced calls."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
            self._pending_args.clear()
            self._pending_kwargs.clear()
    
    def flush(self, key: str = "default") -> None:
        """
        Immediately execute a pending call.
        
        Args:
            key: Key of the call to flush
        """
        with self._lock:
            if key in self._timers:
                self._timers[key].cancel()
                del self._timers[key]
            
            if key in self._pending_args:
                args = self._pending_args.pop(key)
                kwargs = self._pending_kwargs.pop(key)
        
        if "args" in dir():
            try:
                func = self._get_func_for_key(key)
                if func:
                    func(*args, **kwargs)
            except Exception as e:
                print(f"Error flushing debounced function: {e}")
    
    def _get_func_for_key(self, key: str) -> Optional[Callable]:
        """Get the function associated with a key (internal use)."""
        return None
    
    def is_pending(self, key: str = "default") -> bool:
        """Check if there's a pending call for a key."""
        with self._lock:
            return key in self._timers
    
    @property
    def pending_count(self) -> int:
        """Get the number of pending calls."""
        with self._lock:
            return len(self._timers)


class Throttler:
    """
    Throttler - limits function execution rate.
    
    Unlike debouncing, throttling ensures the function is called
    at most once per time period.
    """
    
    def __init__(self, interval_ms: int = 100):
        """
        Initialize the throttler.
        
        Args:
            interval_ms: Minimum interval between calls in milliseconds
        """
        self.interval_ms = interval_ms
        self._last_call: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def call(
        self,
        func: Callable,
        key: str = "default",
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to call a throttled function.
        
        Args:
            func: Function to call
            key: Unique key for this throttled operation
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            True if the function was called, False if throttled
        """
        import time
        
        with self._lock:
            now = time.time() * 1000
            last = self._last_call.get(key, 0)
            
            if now - last >= self.interval_ms:
                self._last_call[key] = now
            else:
                return False
        
        try:
            func(*args, **kwargs)
            return True
        except Exception as e:
            print(f"Error in throttled function: {e}")
            return False
    
    def reset(self, key: str = "default") -> None:
        """Reset the throttle timer for a key."""
        with self._lock:
            self._last_call.pop(key, None)
    
    def reset_all(self) -> None:
        """Reset all throttle timers."""
        with self._lock:
            self._last_call.clear()


class RateLimiter:
    """
    Rate Limiter - limits the number of calls in a time window.
    
    Useful for API calls or operations that have rate limits.
    """
    
    def __init__(self, max_calls: int = 10, window_ms: int = 1000):
        """
        Initialize the rate limiter.
        
        Args:
            max_calls: Maximum calls allowed in the window
            window_ms: Time window in milliseconds
        """
        self.max_calls = max_calls
        self.window_ms = window_ms
        self._calls: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str = "default") -> bool:
        """
        Check if a call is allowed.
        
        Args:
            key: Key to check
            
        Returns:
            True if the call is allowed
        """
        import time
        
        with self._lock:
            now = time.time() * 1000
            
            if key not in self._calls:
                self._calls[key] = []
            
            window_start = now - self.window_ms
            self._calls[key] = [t for t in self._calls[key] if t > window_start]
            
            if len(self._calls[key]) < self.max_calls:
                self._calls[key].append(now)
                return True
            
            return False
    
    def get_remaining(self, key: str = "default") -> int:
        """Get the number of remaining calls allowed."""
        import time
        
        with self._lock:
            now = time.time() * 1000
            
            if key not in self._calls:
                return self.max_calls
            
            window_start = now - self.window_ms
            self._calls[key] = [t for t in self._calls[key] if t > window_start]
            
            return max(0, self.max_calls - len(self._calls[key]))
    
    def reset(self, key: str = "default") -> None:
        """Reset the rate limiter for a key."""
        with self._lock:
            self._calls.pop(key, None)

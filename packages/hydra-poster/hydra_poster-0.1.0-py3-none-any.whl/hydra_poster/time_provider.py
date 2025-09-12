"""Time abstraction for testable time operations."""

import time as _time
from abc import ABC, abstractmethod


class TimeProvider(ABC):
    """Abstract interface for time operations to enable testing without delays."""

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        pass

    @abstractmethod
    def time(self) -> float:
        """Return the current time in seconds since the Unix epoch."""
        pass


class RealTimeProvider(TimeProvider):
    """Production time provider that uses actual system time."""

    def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        _time.sleep(seconds)

    def time(self) -> float:
        """Return the current time in seconds since the Unix epoch."""
        return _time.time()


class TestTimeProvider(TimeProvider):
    """Test time provider that tracks calls without actual delays."""

    def __init__(self, initial_time: float = 0.0) -> None:
        """Initialize with optional starting time."""
        self.current_time = initial_time
        self.sleep_calls: list[float] = []

    def sleep(self, seconds: float) -> None:
        """Record sleep call and advance virtual time."""
        self.sleep_calls.append(seconds)
        self.current_time += seconds

    def time(self) -> float:
        """Return the current virtual time."""
        return self.current_time

    def advance(self, seconds: float) -> None:
        """Manually advance the virtual clock."""
        self.current_time += seconds

    def reset(self) -> None:
        """Reset all tracked calls and time."""
        self.current_time = 0.0
        self.sleep_calls.clear()

    @property
    def total_sleep_time(self) -> float:
        """Return the total time slept across all calls."""
        return sum(self.sleep_calls)

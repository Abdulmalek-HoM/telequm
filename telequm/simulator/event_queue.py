"""
EventQueue — Priority-based Discrete Event Queue
=================================================

Lightweight priority queue for scheduling simulation events
(e.g., traffic arrivals, mobility updates, optimization runs).
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, List, Optional


class EventType(Enum):
    """Categories of simulation events."""
    CHANNEL_UPDATE = auto()
    TRAFFIC_UPDATE = auto()
    MOBILITY_UPDATE = auto()
    OPTIMIZATION_RUN = auto()
    METRIC_COLLECTION = auto()
    USER_ARRIVAL = auto()
    USER_DEPARTURE = auto()
    CUSTOM = auto()


@dataclass(order=True)
class Event:
    """
    A single simulation event.
    
    Attributes
    ----------
    time : int
        Timestep at which the event fires.
    event_type : EventType
        Category of event.
    payload : dict
        Arbitrary data passed to the handler.
    callback : callable, optional
        Function to invoke; signature ``callback(env, event)``.
    """
    time: int
    priority: int = field(compare=True, default=0)
    event_type: EventType = field(compare=False, default=EventType.CUSTOM)
    payload: dict = field(compare=False, default_factory=dict)
    callback: Optional[Callable] = field(compare=False, default=None, repr=False)


class EventQueue:
    """
    Min-heap event queue for the simulation engine.
    
    Events are popped in order of ``(time, priority)`` so that
    ties at the same timestep are broken deterministically.
    
    Example
    -------
    >>> eq = EventQueue()
    >>> eq.schedule(Event(time=5, event_type=EventType.TRAFFIC_UPDATE))
    >>> ev = eq.pop()
    """

    def __init__(self):
        self._heap: List[Event] = []
        self._counter: int = 0          # tie-break for equal (time, priority)

    def schedule(self, event: Event) -> None:
        """Add an event to the queue."""
        heapq.heappush(self._heap, event)

    def schedule_recurring(
        self,
        event_type: EventType,
        start: int,
        interval: int,
        end: int,
        payload: Optional[dict] = None,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Schedule a recurring event from *start* to *end* (inclusive)
        at every *interval* timesteps.
        """
        t = start
        while t <= end:
            self.schedule(Event(
                time=t,
                event_type=event_type,
                payload=payload or {},
                callback=callback,
            ))
            t += interval

    def pop(self) -> Event:
        """Remove and return the next event."""
        return heapq.heappop(self._heap)

    def peek(self) -> Optional[Event]:
        """Return next event without removing it."""
        return self._heap[0] if self._heap else None

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        self._heap.clear()

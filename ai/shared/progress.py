"""Run-scoped progress + provenance, carried in a ContextVar.

The API sets a Run before starting a pipeline thread (asyncio.to_thread copies
the context); the LLM gateway reports each structured call into it and the API
forwards those events to the client. `used_mock` records whether any call fell
through to the offline mock provider, so a result can never silently pass fake
data off as live.
"""

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class Run:
    sink: Callable[[dict[str, Any]], None] = lambda event: None
    crew: Optional[str] = None
    used_mock: bool = False
    sources: Optional[Any] = None  # evidence.sources.SourcePool shared by every crew

    def emit(self, **event: Any) -> None:
        self.sink({"crew": self.crew, **event})


_current: ContextVar[Optional[Run]] = ContextVar("ai_run", default=None)


def start_run(sink: Callable[[dict[str, Any]], None] | None = None) -> Run:
    run = Run(sink=sink or (lambda event: None))
    _current.set(run)
    return run


def current_run() -> Optional[Run]:
    return _current.get()

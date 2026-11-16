"""In-memory conversation state kept between chat messages.

Each conversation remembers the client the user identified as and, while the
chatbot is asking for missing details, the partially specified request.
State lives only in process memory (never in the database), so an incomplete
order can never be persisted. Conversations expire after an idle TTL.
"""

from collections.abc import Callable
from dataclasses import dataclass, field, replace
import threading
import time
from typing import Literal
import uuid

from app.schemas import ExtractedEntities, ParserSource

PendingIntent = Literal["order", "stock_query"]

DEFAULT_TTL_SECONDS = 15 * 60
DEFAULT_MAX_ENTRIES = 10_000


@dataclass
class PendingRequest:
    """A partially specified request waiting for the user to supply missing slots."""

    intent: PendingIntent
    entities: ExtractedEntities = field(default_factory=ExtractedEntities)
    confidence: float = 1.0
    source: ParserSource = "fallback"
    attempts: int = 0


@dataclass
class ConversationState:
    """Everything remembered about one conversation."""

    client: str | None = None
    pending: PendingRequest | None = None
    updated_at: float = 0.0

    @property
    def is_empty(self) -> bool:
        return self.client is None and self.pending is None


class ConversationStore:
    """Thread-safe, TTL-bound store of conversation state keyed by conversation id."""

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock
        self._lock = threading.Lock()
        self._items: dict[str, ConversationState] = {}

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex

    def _evict_expired(self, now: float) -> None:
        expired = [
            cid for cid, item in self._items.items() if now - item.updated_at > self._ttl_seconds
        ]
        for cid in expired:
            del self._items[cid]

    def get(self, conversation_id: str | None) -> ConversationState | None:
        """Return a copy of the conversation state, or None if missing/expired."""
        if not conversation_id:
            return None
        with self._lock:
            self._evict_expired(self._clock())
            return _copy(self._items.get(conversation_id))

    def save(self, conversation_id: str, state: ConversationState) -> None:
        """Store the state; an empty state removes the conversation instead."""
        with self._lock:
            now = self._clock()
            self._evict_expired(now)
            if state.is_empty:
                self._items.pop(conversation_id, None)
                return
            state.updated_at = now
            self._items[conversation_id] = _copy(state)
            if len(self._items) > self._max_entries:
                oldest = min(self._items, key=lambda cid: self._items[cid].updated_at)
                del self._items[oldest]

    def clear(self, conversation_id: str | None) -> None:
        if not conversation_id:
            return
        with self._lock:
            self._items.pop(conversation_id, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


def _copy(state: ConversationState | None) -> ConversationState | None:
    """Return a detached copy so callers cannot mutate stored state in place."""
    if state is None:
        return None
    pending = state.pending
    if pending is not None:
        pending = replace(pending, entities=pending.entities.model_copy())
    return replace(state, pending=pending)


conversation_store = ConversationStore()


def get_conversation_store() -> ConversationStore:
    """FastAPI dependency returning the process-wide conversation store."""
    return conversation_store

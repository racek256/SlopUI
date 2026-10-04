import asyncio
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Generation:
    chat_id: str
    status: str # running | done | error 
    events: list[str] = field(default_factory=list)
    subscribers: set = field(default_factory=set)

GENERATIONS: dict[str,Generation] = {}

def publish(gen, event):
    gen.events.append(event)
    for q in gen.subscribers:
        q.put_nowait(event)

DONE = object()

async def event_stream(gen, timeout: float = 120.0):
    q = asyncio.Queue()
    events_so_far = list(gen.events)
    gen.subscribers.add(q)
    try:
        for e in events_so_far:
            yield e 
        while True:
            try:
                e = await asyncio.wait_for(q.get(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("event_stream timeout (chat_id=%s, status=%s)", gen.chat_id, gen.status)
                yield json.dumps({"error": "stream timeout: no events from generation", "type": "StreamTimeout"}) + "\n"
                break
            if e is DONE:
                break
            yield e 
    finally:
        gen.subscribers.discard(q)


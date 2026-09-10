import asyncio
from dataclasses import dataclass, field

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

async def event_stream(gen):
    q = asyncio.Queue()
    events_so_far = list(gen.events)
    gen.subscribers.add(q)
    try:
        for e in events_so_far:
            yield e 
        while True:
            e = await q.get()
            if e is DONE:
                break
            yield e 
    finally:
        gen.subscribers.discard(q)


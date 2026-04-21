import asyncio

streams = {}

def create_stream(session_id):
    q = asyncio.Queue()
    streams[session_id] = q
    return q

async def push_event(session_id, data):
    if session_id in streams:
        await streams[session_id].put(data)

def get_stream(session_id):
    return streams.get(session_id)
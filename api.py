# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from stream_manager import create_stream
from contextlib import asynccontextmanager

main_loop = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://multi-agent-ui-sigma.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
async def health_check():
    print("Health check endpoint hit")
    return {"status": "ok"}

class ResearchRequest(BaseModel):
    topic: str
    model: str
    session_id: str

class ResearchResponse(BaseModel):
    search_results: str
    scraped_content: str
    report: str
    feedback: str
    debate: str

@app.post("/api/research")
async def research(request: ResearchRequest):
    from pipeline import run_research_pipeline

    try:
        state = await asyncio.to_thread(
            run_research_pipeline,
            request.topic,
            request.model,
            request.session_id,
            main_loop
        )   
        return state

    except Exception as e:
        msg = str(e).lower()
        print(f"Error in research pipeline: {msg}")

        # 🧠 token limit
        if "request too large" in msg or "tokens" in msg:
            return JSONResponse(
                status_code=413,
                content={
                    "type": "token_limit",
                    "message": "Request is too large for this model.",
                    "suggestion": "Switch to a different model."
                }
            )

        # ⚡ rate limit
        if "rate_limit" in msg or "rate limit" in msg:
            return JSONResponse(
                status_code=429,
                content={
                    "type": "rate_limit",
                    "message": "Rate limit exceeded.",
                    "suggestion": "Switch to a different model."
                }
            )

        # 🔐 auth / API key
        if "api key" in msg or "unauthorized" in msg:
            return JSONResponse(
                status_code=401,
                content={
                    "type": "auth_error",
                    "message": "Authentication failed for model.",
                    "suggestion": "Switch to a different model."
                }
            )

        # 🧩 fallback
        return JSONResponse(
            status_code=500,
            content={
                "type": "unknown_error",
                "message": "Something went wrong while processing your request.",
                "suggestion": "Try again or switch to a different model."
            }
        )
        

@app.get("/api/stream/{session_id}")
async def stream(session_id: str):

    queue = create_stream(session_id)

    async def event_generator():
        while True:
            data = await queue.get()
            yield f"data: {json.dumps(data)}\n\n"

            if data.get("type") == "done":
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
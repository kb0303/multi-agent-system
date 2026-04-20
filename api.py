# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

class ResearchRequest(BaseModel):
    topic: str
    model: str

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
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(
            None,
            run_research_pipeline,
            request.topic,
            request.model
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
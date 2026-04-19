# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

app = FastAPI()

# Allow Next.js dev server to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    from pipeline import run_research_pipeline

    loop = asyncio.get_event_loop()
    state = await loop.run_in_executor(None, run_research_pipeline, request.topic, request.model)
    return state
# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pipeline import run_research_pipeline
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

class ResearchResponse(BaseModel):
    search_results: str
    scraped_content: str
    report: str
    feedback: str

@app.post("/api/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    # Run the blocking pipeline in a thread so FastAPI stays responsive
    loop = asyncio.get_event_loop()
    state = await loop.run_in_executor(None, run_research_pipeline, request.topic)
    return state
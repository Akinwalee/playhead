import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from typing import List, Dict

from scraper import YouTubeScraper
from rag import rag_system
from db import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube RAG Chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    url: str
    session_id: str | None = None

class ChatRequest(BaseModel):
    query: str
    session_id: str

class ChatResponse(BaseModel):
    answer: str

class SessionResponse(BaseModel):
    session_id: str

scraper = YouTubeScraper()
db = Database()


def process_ingest(session_id: str, url: str) -> List[Dict]:
    logger.info(f"Starting ingestion for session {session_id}: {url}")
    data = scraper.scrape(url)
    if not data:
        logger.warning("No data scraped.")
        raise ValueError("No content found at URL")
    
    rag_system.ingest(session_id, data)
    
    video_list = []
    for video in data:
        video_info = {
            "video_id": video['video_id'],
            "title": video.get('title', 'Unknown Title'),
            "url": video['url']
        }
        db.add_video(session_id, video_info)
        video_list.append(video_info)

    logger.info("Ingestion completed.")
    return video_list

@app.post("/ingest")
async def ingest_endpoint(request: IngestRequest):
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid4())
        logger.info(f"Generated new session_id: {session_id}")
    
    try:
        videos = process_ingest(session_id, request.url)
        return {"message": "Ingestion successful.", "session_id": session_id, "videos": videos}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/session/{session_id}/videos")
def get_session_videos(session_id: str):
    return {"videos": db.get_videos(session_id)}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer = rag_system.chat(request.session_id, request.query)
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session", response_model=SessionResponse)
def create_session():
    return {"session_id": str(uuid4())}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper import YouTubeScraper
from rag import rag_system

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

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

scraper = YouTubeScraper()

def background_ingest(url: str):
    logger.info(f"Starting background ingestion for: {url}")
    try:
        data = scraper.scrape(url)
        if not data:
            logger.warning("No data scraped.")
            return
        rag_system.ingest(data)
        logger.info("Background ingestion completed.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")

@app.post("/ingest")
async def ingest_endpoint(request: IngestRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(background_ingest, request.url)
    return {"message": "Ingestion started in background."}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer = rag_system.chat(request.query)
        return ChatResponse(answer=answer)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import logging
from typing import List, Dict

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

logger = logging.getLogger(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "yt-rag-chat")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not PINECONE_API_KEY or not GOOGLE_API_KEY:
    logger.error("Missing API Keys in environment variables.")

from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGSystem:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self._init_index()
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

    def _init_index(self):
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        
        if PINECONE_INDEX_NAME not in existing_indexes:
            logger.info(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
            try:
                self.pc.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimension=768,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
        
        return self.pc.Index(PINECONE_INDEX_NAME)

    def ingest(self, session_id: str, scraped_data: List[Dict]):
        """Ingests scraped video transcripts into Pinecone."""
        vectors = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        
        for item in scraped_data:
            chunks = text_splitter.split_text(item['text'])
            for i, chunk in enumerate(chunks):
                vector_values = self.embeddings.embed_query(chunk)
                vector_id = f"{session_id}_{item['video_id']}_{i}"
                metadata = {
                    "text": chunk,
                    "source": item['url'],
                    "video_id": item['video_id'],
                    "session_id": session_id
                }
                vectors.append((vector_id, vector_values, metadata))
        
        if vectors:
            logger.info(f"Upserting {len(vectors)} vectors to Pinecone for session {session_id}...")

            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                self.index.upsert(vectors=batch)
            logger.info("Ingestion complete.")
        else:
            logger.warning("No documents to ingest.")

    def chat(self, session_id: str, query: str):
        """Answers a question based on retrieved context."""
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            filter={"session_id": session_id}
        )
        
        context_parts = []
        for match in results.matches:
            if match.metadata and "text" in match.metadata:
                context_parts.append(match.metadata["text"])
        
        if not context_parts:
            return "I don't have enough context from your ingested videos to answer this question."

        context = "\n\n".join(context_parts)

        logger.info(f"Context: {context}")
        
        system_prompt = (
            "You are a question-answering assistant."
            "Your primary task is to provide accurate, concise, and useful answers based on the retrieved video context provided below."
            "Base your answer primarily on the provided context."
            "If the context doesn't contain sufficient information to answer fully, acknowledge this limitation."
            "If the question cannot be answered using the context, clearly state \"I don't know\" or \"The provided context doesn't contain information about this.\""
            "Keep answers concise (2-4 sentences typically) while ensuring completeness."
            "Maintain a helpful, neutral tone. Avoid speculation beyond what the context supports."
            "Do not reproduce harmful, unethical, or dangerous content from the context."
            "If such content appears, respond appropriately without endorsing or amplifying it."
            "If relevant, you may use bullet points for clarity, but prioritize straightforward prose."
            "\n\nContext:\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm
        response = chain.invoke({"context": context, "input": query})
        
        return response.content

rag_system = RAGSystem()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from ingestion import OpenStackLogIngestor
from embeddings import LogVectorStore
from rag_engine import RAGDiagnosticEngine

# Load the environment variables (.env)
load_dotenv()

# Initialize our core application
app = FastAPI(title="LogRAG Sentinel API")

# Initialize our singleton engine instances globally so they stay in memory 
# while the server is running.
ingestor = OpenStackLogIngestor(chunk_size=300, overlap=50)
vector_store = LogVectorStore()
rag_engine = RAGDiagnosticEngine()

# --- Pydantic Data Models for Request Validation ---
class IngestRequest(BaseModel):
    file_path: str

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

# --- API Endpoints ---

@app.post("/api/ingest")
async def ingest_logs(request: IngestRequest):
    """Endpoint to trigger the ingestion and embedding of a log file."""
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="Log file not found locally.")
    
    try:
        # 1. Parse the logs
        chunks = ingestor.parse_file(request.file_path)
        
        # 2. Add to FAISS Vector Store
        vector_store.add_chunks(chunks)
        
        return {
            "status": "success", 
            "message": f"Successfully ingested and embedded {len(chunks)} chunks.",
            "total_vectors_in_db": vector_store.index.ntotal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_query(request: QueryRequest):
    """Endpoint to search the vector database and generate a RAG analysis."""
    if vector_store.index.ntotal == 0:
        raise HTTPException(status_code=400, detail="Vector database is empty. Ingest logs first.")
        
    try:
        # 1. Retrieve the nearest log chunks
        retrieved_chunks = vector_store.search(request.query, top_k=request.top_k)
        
        # 2. Generate the grounded analysis
        analysis = rag_engine.generate_analysis(request.query, retrieved_chunks)
        
        return {
            "status": "success",
            "query": request.query,
            "analysis": analysis,
            # Returning the raw retrieved sources back to React so we can display them!
            "sources_used": [chunk['text'] for chunk in retrieved_chunks] 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


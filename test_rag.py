import os
from dotenv import load_dotenv
from ingestion import OpenStackLogIngestor
from embeddings import LogVectorStore
from rag_engine import RAGDiagnosticEngine

# THIS IS THE MAGIC LINE: It loads the variables from .env into os.environ
load_dotenv()

if __name__ == "__main__":
    # Ensure the API key loaded successfully to prevent crashes
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("❌ GROQ_API_KEY is missing! Please add it to your .env file.")

    # 1. Dummy logs mimicking the dataset, including an IP address and Email to test the guardrail
    sample_logs = """
    nova-compute.log.1 2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [instance: b900] VM Started from IP 192.168.1.50
    nova-compute.log.1 2017-05-16 00:00:05.100 2931 ERROR nova.compute.manager [instance: b900] VM Crashed OutOfMemory. Contact admin@openstack.org.
    """
    
    print("--- 1. INGESTION ---")
    ingestor = OpenStackLogIngestor(chunk_size=50, overlap=0)
    chunks = ingestor.parse_string(sample_logs)
    
    print("\n--- 2. VECTOR SEARCH ---")
    vector_store = LogVectorStore()
    vector_store.add_chunks(chunks)
    
    query = "Why did the virtual machine fail and who should I contact?"
    retrieved_data = vector_store.search(query, top_k=1)
    
    print("\n--- 3. RAG DIAGNOSTICS ---")
    rag = RAGDiagnosticEngine()
    analysis = rag.generate_analysis(query, retrieved_data)
    
    print("\n================ AI ANALYSIS ================\n")
    print(analysis)
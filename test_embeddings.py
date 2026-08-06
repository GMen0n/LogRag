from ingestion import OpenStackLogIngestor
from embeddings import LogVectorStore

if __name__ == "__main__":
    # 1. Reuse our ingestor to get chunks from the string
    sample_logs = """
    nova-compute.log.1 2017-05-16 00:00:04.500 2931 INFO nova.compute.manager [instance: b900] VM Started
    nova-compute.log.1 2017-05-16 00:00:05.100 2931 ERROR nova.compute.manager [instance: b900] VM Crashed OutOfMemory
    nova-api.log.1 2017-05-16 00:00:06.000 25746 INFO nova.osapi_compute HTTP 200 OK
    """
    
    ingestor = OpenStackLogIngestor(chunk_size=15, overlap=0)
    chunks = ingestor.parse_string(sample_logs)
    
    # 2. Initialize our Vector Store
    vector_store = LogVectorStore()
    
    # 3. Add chunks to FAISS
    vector_store.add_chunks(chunks)
    
    # 4. Perform a semantic search! 
    # Notice we don't use the exact word "Crashed" in our query.
    query = "Why did the virtual machine fail?"
    print(f"\n🔍 Searching for: '{query}'")
    
    results = vector_store.search(query, top_k=1)
    print("\n🏆 Top Result:")
    print(results[0]['text'])
    print(f"Distance Score: {results[0]['distance']} (Lower is closer)")
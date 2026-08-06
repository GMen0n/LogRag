import numpy as np
import faiss
from typing import List, Dict
from fastembed import TextEmbedding

class LogVectorStore:
    """
    Handles local vector embedding generation using FastEmbed and manages
    an in-memory FAISS index for efficient semantic similarity search.
    """
    def __init__(self):
        print("Loading local FastEmbed model (BAAI/bge-small-en-v1.5)...")
        
        # FastEmbed runs completely offline on the CPU, so no API keys,
        # internet connection, or external embedding service is required.
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # The selected BAAI embedding model produces fixed-size
        # 384-dimensional dense vector representations.
        self.dimension = 384 
        
        # Initialize an empty FAISS index that performs similarity search
        # using L2 (Euclidean) distance between embedding vectors.
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # FAISS stores only numerical vectors internally, so this dictionary
        # maintains a mapping from FAISS vector IDs to the original text
        # chunks and any associated metadata.
        self.chunk_storage: Dict[int, Dict] = {}
        
        # Counter used to assign a unique integer ID to every stored chunk.
        self.current_id = 0

    def add_chunks(self, chunks: List[Dict]):
        """Converts text chunks into embeddings and indexes them in FAISS."""
        if not chunks:
            return

        print(f"Generating embeddings for {len(chunks)} log chunks...")
        
        # Extract only the raw text content from each chunk dictionary,
        # since the embedding model accepts plain text as input.
        documents = [chunk['text'] for chunk in chunks]
        
        # FastEmbed returns embeddings as a generator. Convert it into
        # a list so the vectors can be processed further.
        embeddings_list = list(self.embedding_model.embed(documents))
        
        # Stack all embeddings into a contiguous 2D NumPy array and convert
        # them to float32, which is the datatype expected by FAISS.
        embeddings_np = np.vstack(embeddings_list).astype(np.float32)
        
        # Insert all embedding vectors into the FAISS index so they become
        # available for future similarity searches.
        self.index.add(embeddings_np)
        
        # Store each original chunk in the local dictionary using the same
        # integer IDs that correspond to their position inside the FAISS index.
        for idx, chunk in enumerate(chunks):
            self.chunk_storage[self.current_id + idx] = chunk
            
        # Advance the ID counter so the next batch of chunks receives
        # a new set of unique identifiers.
        self.current_id += len(chunks)
        
        print(f"Successfully indexed vectors. Total vectors in FAISS: {self.index.ntotal}")

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Embeds a natural language search query and retrieves top-k matching log chunks."""
        if self.index.ntotal == 0:
            return []

        # Convert the natural language query into the same 384-dimensional
        # embedding space used for the indexed log chunks.
        query_embedding = list(self.embedding_model.embed([query]))[0]
        
        # FAISS expects the query vector to be provided as a 2D float32
        # NumPy array with shape (1, embedding_dimension).
        query_np = np.array([query_embedding], dtype=np.float32)
        
        # Perform a nearest-neighbor search to retrieve the top-k vectors
        # with the smallest L2 distance from the query embedding.
        distances, indices = self.index.search(query_np, top_k)
        
        # Translate the returned FAISS vector IDs back into the original
        # log chunks stored in the local dictionary.
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                chunk_data = self.chunk_storage[idx].copy()
                
                # Include the distance score in the returned result for
                # debugging and observability purposes. A lower distance
                # indicates a closer semantic match.
                chunk_data['distance'] = float(distances[0][i])
                results.append(chunk_data)
                
        return results
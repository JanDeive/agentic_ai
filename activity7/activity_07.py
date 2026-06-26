import os
import re
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

COLLECTION_NAME = "activity7_memory"
VECTOR_SIZE = 8  # Match the size of our custom vocabulary matrix

SOURCE_TEXT = """
Qdrant is a vector database designed for similarity search and retrieval.

Chunking is the process of dividing a document into smaller pieces before embedding.
If a chunk is too large, it may contain too much unrelated information.
If a chunk is too small, it may lose the surrounding context needed for the answer.

Overlap helps preserve meaning when a sentence or idea crosses a boundary.
Metadata such as source, section, and strategy makes debugging easier.
"""


# =============================================================================
# Step 2: Strategy 1 – Fixed-Size Chunking
# =============================================================================

def fixed_size_chunk(text: str, chunk_size: int = 140, overlap: int = 30) -> list[str]:
    """Split text into overlapping character windows."""
    chunks: list[str] = []
    start = 0

    while start < len(text):
        # 1. Determine the end boundary (don't exceed the text length)
        end = min(start + chunk_size, len(text))

        # 2. Extract and clean the current chunk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # If we've reached the end of the text, stop.
        if end == len(text):
            break

        # Advance start by (chunk_size - overlap), guaranteeing forward progress.
        start = end - overlap

        # Guard against negative or non-advancing start (e.g. overlap >= chunk_size).
        if start <= 0:
            start = end

    return chunks


# =============================================================================
# Step 3: Strategy 2 – Structural Paragraph Chunking
# =============================================================================

def paragraph_chunk(text: str) -> list[str]:
    """Split text on blank line boundaries."""
    # Regex pattern that matches one or more newlines separating paragraphs.
    # \n\s*\n matches two newlines with optional whitespace between them.
    regex_pattern = r"\n\s*\n"

    paragraphs = [p.strip() for p in re.split(regex_pattern, text) if p.strip()]
    return paragraphs


# =============================================================================
# Step 4: The Embedding Generator
# =============================================================================

def embed_text(text: str) -> list[float]:
    """Create a tiny deterministic 8-dimension vector representation."""
    vocab = ["qdrant", "chunking", "embedding", "overlap", "metadata",
             "retrieval", "context", "vector"]
    lowered = text.lower()
    vector = [float(lowered.count(word)) for word in vocab]

    # Calculate the vector magnitude (Euclidean norm)
    norm = sum(v * v for v in vector) ** 0.5
    if norm == 0:
        return [0.0 for _ in vector]

    # Normalize: divide every element by the norm so the vector has unit length.
    return [v / norm for v in vector]


# =============================================================================
# Step 5: Storing Points with Metadata in Qdrant
# =============================================================================

def store_chunks(client, collection_name: str, chunks: list[str], strategy: str) -> None:
    """Insert each chunk into Qdrant with metadata payloads."""
    points = []

    # Strategy prefix for generating unique integer IDs across both strategies:
    # "fixed_size" -> offset 0, "paragraph" -> offset 1000
    id_offset = 0 if strategy == "fixed_size" else 1000

    for index, chunk in enumerate(chunks):
        points.append(
            PointStruct(
                id=id_offset + index,        # Integer ID required by in-memory client
                vector=embed_text(chunk),
                payload={
                    "text": chunk,           # Raw text content of the chunk
                    "strategy": strategy,    # Which chunking strategy produced this chunk
                    "chunk_index": index,    # Numerical sequence position
                    "source": "sample_doc", # Origin document identifier
                },
            )
        )

    client.upsert(collection_name=collection_name, points=points)


# =============================================================================
# Step 6: Querying Vector Space
# =============================================================================

def retrieve_best_match(client, collection_name: str, query_vector: list[float]):
    """Query the collection and return the single top-scoring result."""
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=1,
        with_payload=True,
        with_vectors=False,
    )
    return result.points[0] if result.points else None


# =============================================================================
# Step 7: Orchestration & Analysis
# =============================================================================

def main():
    # Initialize connection — uses in-memory mode when QDRANT_URL is not set,
    # so no Docker installation is required for local testing.
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        client = QdrantClient(url=qdrant_url)
    else:
        client = QdrantClient(":memory:")

    # Reset collection space
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        client.delete_collection(collection_name=COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    # Process strategies
    fixed_chunks = fixed_size_chunk(SOURCE_TEXT)
    paragraph_chunks = paragraph_chunk(SOURCE_TEXT)

    # Print out splits for review
    print("--- Fixed-size Chunks ---")
    for i, chunk in enumerate(fixed_chunks):
        print(f"  {i}: {chunk}")

    print("\n--- Paragraph Chunks ---")
    for i, chunk in enumerate(paragraph_chunks):
        print(f"  {i}: {chunk}")

    # Write to DB
    store_chunks(client, COLLECTION_NAME, fixed_chunks, "fixed_size")
    store_chunks(client, COLLECTION_NAME, paragraph_chunks, "paragraph")

    # Target Query
    query_text = "Why does overlap help when chunking a document?"
    query_vector = embed_text(query_text)

    match = retrieve_best_match(client, COLLECTION_NAME, query_vector)

    print(f"\nQuery: {query_text}")
    if match:
        payload = match.payload
        print(f"\nBest Match Strategy Found: [ {payload.get('strategy').upper()} ]")
        print(f"Chunk Index Location: {payload.get('chunk_index')}")
        print(f"Text Returned:\n\"{payload.get('text')}\"")


if __name__ == "__main__":
    main()

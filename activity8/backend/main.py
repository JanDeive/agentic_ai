import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from google import genai
from google.genai import types

from llama_index.core import Document
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.google import GeminiEmbedding

load_dotenv()

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in your .env file.")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# In-memory Qdrant — no Docker required
qdrant_client = QdrantClient(":memory:")

COLLECTION_NAME = "rag_documents"
VECTOR_SIZE = 3072  # gemini-embedding-001 output size

qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="RAG Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """Generate a Gemini embedding vector for the given text."""
    response = gemini_client.models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return response.embeddings[0].values


def semantic_chunk(text: str) -> list[str]:
    """Split text into semantic chunks using LlamaIndex's SemanticSplitterNodeParser.
    Groups sentences into topic-coherent windows before cutting, preserving meaning
    across boundaries better than fixed-size chunking.
    """
    embed_model = GeminiEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=GEMINI_API_KEY,
    )
    splitter = SemanticSplitterNodeParser(
        buffer_size=3,                        # Groups nearby sentences to smooth over short fragments
        breakpoint_percentile_threshold=90,   # Cuts only when topic shifts clearly
        embed_model=embed_model,
    )
    doc = Document(text=text)
    nodes = splitter.get_nodes_from_documents([doc])
    return [node.text.strip() for node in nodes if node.text.strip()]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept a plain-text file, chunk it, embed each chunk, store in Qdrant."""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported.")

    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    chunks = semantic_chunk(text)
    points: list[PointStruct] = []

    for chunk in chunks:
        try:
            vector = get_embedding(chunk, task_type="RETRIEVAL_DOCUMENT")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Embedding API error: {str(e)}")
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk,
                    "source": file.filename,
                },
            )
        )

    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {
        "message": f"Uploaded and indexed '{file.filename}' as {len(chunks)} chunks.",
        "chunks": len(chunks),
    }


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    """RAG chat: retrieve relevant chunks then answer with Gemini."""
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 1. Embed the query
    query_vector = get_embedding(query, task_type="RETRIEVAL_QUERY")

    # 2. Search Qdrant
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=4,
        score_threshold=0.60,
        with_payload=True,
    ).points

    # 3. If nothing relevant found, say so
    if not results:
        return {"answer": "I don't know. The prompt is not relevant to the uploaded data."}

    # 4. Build context block
    context_parts = [
        f"[Source: {hit.payload['source']}]\n{hit.payload['text']}"
        for hit in results
    ]
    context = "\n\n---\n\n".join(context_parts)

    # 5. Generate answer with Gemini
    system_instruction = (
        "You are a helpful assistant that answers questions strictly based on "
        "the provided document context. If the answer cannot be found in the "
        "context, respond with exactly: "
        "'I don't know. The prompt is not relevant to the uploaded data.' "
        "Do not make up information."
    )

    prompt = f"Context:\n{context}\n\nQuestion: {query}"

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        ),
    )

    return {"answer": response.text, "chunks_used": len(results)}

# Activity 7 – RAG Chat App

A single-page React app backed by a FastAPI server. Upload a `.txt` file, and the AI answers questions grounded exclusively in that document.

## Architecture

```
frontend/   React + Vite SPA
backend/    FastAPI + Qdrant (in-memory) + Google Gemini
```

**Flow**
1. User uploads a `.txt` file → backend chunks it → embeds each chunk with Gemini → stores in Qdrant.
2. User sends a question → backend embeds query → searches Qdrant → sends top chunks + question to Gemini → returns grounded answer.
3. If no relevant chunks pass the similarity threshold, the API returns *"I don't know. The prompt is not relevant to the uploaded data."*

---

## Setup

### 1. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## Usage

1. Click **Choose .txt File** in the sidebar and select a plain text document.
2. Wait for the *"indexed (N chunks)"* confirmation.
3. Type a question in the chat box and press **Enter** or **Send**.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server health check |
| POST | `/upload` | Upload and index a `.txt` file |
| POST | `/chat` | Ask a question about indexed documents |

### POST /upload
- Body: `multipart/form-data` with field `file`
- Returns: `{ "message": "...", "chunks": N }`

### POST /chat
- Body: `{ "message": "your question" }`
- Returns: `{ "answer": "..." }`

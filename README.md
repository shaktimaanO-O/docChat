# LangGraph RAG Agent

A document-aware AI assistant built with FastAPI, Streamlit, LangGraph, Pinecone, Groq, and Tavily.

The project lets users upload PDF documents, index them in a Pinecone vector database, and chat with an agent that can answer from the uploaded knowledge base. When enabled, the agent can also use Tavily web search for questions that need fresh or external information.

## Table Of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running The Project](#running-the-project)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Agent Workflow](#agent-workflow)
- [Evaluation](#evaluation)

## Features

- PDF upload and indexing
- Pinecone-backed vector search
- HuggingFace sentence-transformer embeddings
- LangGraph agent workflow
- Groq-powered routing, judging, and answer generation
- Optional Tavily web search
- FastAPI backend with Swagger docs
- Streamlit frontend for document upload and chat
- Agent trace events returned with every chat response
- Automatic Pinecone index creation when missing
- Basic RAG evaluation script with faithfulness, groundedness, relevance, and latency metrics

## Architecture

```text
                  +-------------------+
                  | Streamlit frontend|
                  +---------+---------+
                            |
                            v
                  +-------------------+
                  | FastAPI backend   |
                  +----+---------+----+
                       |         |
        PDF upload ----+         +---- Chat request
                       |         |
                       v         v
              +-------------+  +----------------+
              | PyPDFLoader |  | LangGraph agent|
              +------+------+  +-------+--------+
                     |                 |
                     v                 v
              +-------------+  router -> rag_lookup -> answer
              | Text chunks |       \       \
              +------+------+        \       -> web_search -> answer
                     |                \
                     v                 -> end
              +-------------+
              | Embeddings  |
              +------+------+
                     |
                     v
              +-------------+
              | Pinecone    |
              +-------------+
```

The backend has two main responsibilities:

- `POST /upload-document/` extracts PDF text, chunks it, embeds it, and stores it in Pinecone.
- `POST /chat/` streams a query through a LangGraph workflow and returns the final answer plus trace events.

## Project Structure

```text
basic_prjt/
+-- backend/
|   +-- agent.py             # LangGraph workflow, router, RAG, web search, answer generation
|   +-- config.py            # Backend environment variables
|   +-- main.py              # FastAPI backend routes
|   +-- vectorstore.py       # Pinecone index, embeddings, retrieval, document insertion
+-- frontend/
|   +-- app.py               # Streamlit application entry point
|   +-- backend_api.py       # HTTP client helpers for the backend
|   +-- config.py            # Frontend environment variables
|   +-- session_manager.py   # Streamlit session state setup
|   +-- ui_components.py     # Streamlit UI sections and trace rendering
+-- main.py                  # Minimal root-level healthcheck app
+-- basic_eval.py            # Basic RAG evaluation script
+-- requirements.txt         # Main dependency list
+-- pyproject.toml           # Project metadata
+-- uv.lock                  # uv lockfile
+-- .python-version          # Python version pin
+-- .gitignore
```

## Requirements

- Python 3.12
- uv package manager
- Pinecone account and API key
- Groq API key
- Tavily API key, required only when web search is enabled

## Setup

Clone the repository:

```bash
git clone <your-repository-url>
cd basic_prjt
```

Create a virtual environment:

```bash
uv venv .venv --python 3.12
```

Install dependencies:

```bash
uv pip install -r requirements.txt
```

On Windows, you can activate the environment with:

```powershell
.\.venv\Scripts\activate
```

This project uses `uv`, so it is fine if `.venv` does not expose `python -m pip`.

## Environment Variables

Create a `.env` file in the project root.

```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-index

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

TAVILY_API_KEY=your_tavily_api_key
FASTAPI_BASE_URL=http://127.0.0.1:8000

DOC_SOURCE_DIR=data
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Environment variable notes:

| Variable | Required | Used by | Description |
| --- | --- | --- | --- |
| `PINECONE_API_KEY` | Yes | Backend | Pinecone API key |
| `PINECONE_ENVIRONMENT` | Yes | Backend | Pinecone serverless region, for example `us-east-1` |
| `PINECONE_INDEX_NAME` | Yes | Backend | Vector index name, for example `rag-index` |
| `GROQ_API_KEY` | Yes | Backend | Groq API key |
| `GROQ_MODEL` | No | Backend | Groq model, defaults to `llama-3.3-70b-versatile` |
| `TAVILY_API_KEY` | Yes for web search | Backend | Tavily API key |
| `FASTAPI_BASE_URL` | No | Frontend | Backend URL, defaults to `http://localhost:8000` |
| `DOC_SOURCE_DIR` | No | Backend config | Defaults to `data` |
| `EMBED_MODEL` | No | Backend config | Intended embedding model setting |

Use a Pinecone index name without spaces. Keep `.env` out of Git.

## Running The Project

Start the FastAPI backend first.

```powershell
cd backend
..\.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

The backend docs will be available at:

```text
http://127.0.0.1:8000/docs
```

Start the Streamlit frontend in a second terminal.

```powershell
cd frontend
..\.venv\Scripts\streamlit.exe run app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

Recommended startup order:

1. Start the FastAPI backend.
2. Confirm `GET /health` works.
3. Start the Streamlit frontend.
4. Upload a PDF.
5. Ask questions in the chat UI.

## API Reference

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Upload Document

```http
POST /upload-document/
```

Uploads a PDF document, extracts text with `PyPDFLoader`, chunks the text, embeds it, and stores the vectors in Pinecone.

Request type:

```text
multipart/form-data
```

Form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `file` | File | Yes | PDF file to index |

PowerShell example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/upload-document/" -F "file=@C:\path\to\document.pdf;type=application/pdf"
```

Example response:

```json
{
  "message": "PDF 'document.pdf' successfully uploaded and indexed.",
  "filename": "document.pdf",
  "processed_chunks": 12
}
```

Postman setup:

- Method: `POST`
- URL: `http://127.0.0.1:8000/upload-document/`
- Body: `form-data`
- Key: `file`
- Type: `File`
- Value: select a PDF file

Do not manually set the `Content-Type` header in Postman. Let Postman generate the multipart boundary.

### Chat

```http
POST /chat/
```

Runs the user query through the LangGraph agent.

Request body:

```json
{
  "session_id": "demo-session",
  "query": "What is this document about?",
  "enable_web_search": false
}
```

Fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `session_id` | string | Yes | Conversation identifier |
| `query` | string | Yes | User question |
| `enable_web_search` | boolean | No | Allows Tavily web search when RAG is insufficient |

PowerShell example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/chat/" `
  -H "Content-Type: application/json" `
  -d "{\"session_id\":\"demo-session\",\"query\":\"What is this document about?\",\"enable_web_search\":false}"
```

Example response:

```json
{
  "response": "The document explains ...",
  "trace_events": [
    {
      "step": 1,
      "node_name": "router",
      "description": "Router decided: 'rag'",
      "details": {
        "decision": "rag",
        "reason": "Based on initial query analysis."
      },
      "event_type": "router_decision"
    }
  ]
}
```

## Frontend

The Streamlit frontend provides:

- PDF upload form
- Web search toggle
- Chat interface
- Agent workflow trace viewer
- Session-based chat history

Run it after the backend is already running:

```powershell
cd frontend
..\.venv\Scripts\streamlit.exe run app.py
```

If the backend runs on a different host or port, set:

```env
FASTAPI_BASE_URL=http://127.0.0.1:8000
```

## Agent Workflow

The graph in `backend/agent.py` uses four nodes:

| Node | Purpose |
| --- | --- |
| `router` | Chooses whether to use RAG, web search, direct answer, or end |
| `rag_lookup` | Retrieves relevant chunks from Pinecone and asks an LLM judge if they are sufficient |
| `web_search` | Uses Tavily search when web search is enabled and needed |
| `answer` | Generates the final answer from available context |

Simplified flow:

```text
router
  |-- end
  |-- answer
  |-- rag_lookup -> answer
  |              -> web_search -> answer
  |-- web_search -> answer
```

## Evaluation

A basic RAG evaluation was run using **NIST SP 800-61 Rev. 2: Computer Security Incident Handling Guide** after uploading the PDF through the backend.

The evaluation uses five incident-response questions with web search disabled. For each answer, `basic_eval.py` records:

- Agent route
- Retrieved RAG evidence
- Response latency
- Faithfulness score
- Groundedness score
- Answer relevance score

Scores are judged on a 1 to 5 scale using the retrieved RAG context returned by the API trace.

Latest evaluation summary:

| Metric | Result |
| --- | ---: |
| Questions | 5 |
| Faithfulness | 4.4 / 5 |
| Groundedness | 4.8 / 5 |
| Answer relevance | 5.0 / 5 |
| Average latency | 25.52 sec |

Run the evaluation after the backend is running and the PDF has been uploaded:

```powershell
.\.venv\Scripts\python.exe basic_eval.py
```

The script writes detailed results to:

```text
basic_eval_results.json
```

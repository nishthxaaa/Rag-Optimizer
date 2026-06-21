# RAG Optimizer

An autonomous, self-optimizing document chat application. Upload any PDF and the system automatically finds the best retrieval configuration before you ask a single question.

![Demo](assets/demo.gif)

## What makes it different

Most RAG systems use hardcoded chunk sizes and retrieval settings. This system runs a hidden optimization loop — testing 6 configurations against your document, scoring each one with an LLM judge, and promoting the winner to production automatically.

## How it works

1. **Upload** — drop any PDF into the interface
2. **Optimize** — the system spawns 6 RAG variants with different chunk sizes and retrieval depths
3. **Evaluate** — an LLM judge scores each variant on faithfulness, completeness, and conciseness
4. **Chat** — the winning configuration is locked in and you chat with a highly accurate AI tailored to your document

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Query, Vite |
| Backend | FastAPI, Python 3.10+ |
| LLM | Groq (llama-3.1-8b-instant) |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (local) |
| Vector DB | ChromaDB (local persistent) |
| Orchestration | LangChain |

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend

```bash
cd rag-optimizer
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=your_key_here
```

Start the backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd rag-frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)


## Evaluation criteria

Each RAG variant is scored by an LLM judge on three axes:

| Criterion | What it measures |
|---|---|
| Faithfulness | Is the answer grounded in the retrieved context? |
| Completeness | Does it fully answer the question? |
| Conciseness | Is it free of unnecessary filler? |

The variant with the highest average score across 3 auto-generated test questions is promoted to production.

## Chunking strategies tested

| Name | Chunk size | Overlap |
|---|---|---|
| Small | 256 tokens | 30 tokens |
| Medium | 512 tokens | 50 tokens |
| Large | 1024 tokens | 100 tokens |

## Why this project exists

Most production RAG systems are built with guesswork — developers pick a chunk size, run it once, and ship it. This project treats retrieval configuration as what it actually is: a hyperparameter search problem. The same rigor you would apply to tuning a machine learning model should apply to how an AI reads your documents.


import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_PATH = "chroma_db"

# ── Pre-load embedding model once at startup ──────────────────
# This runs when the server starts, not when the first request comes in.
# Prevents request timeouts on Render free tier.
print("[Config] Pre-loading embedding model...")
_EMBEDDINGS = None

def get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _EMBEDDINGS = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("[Config] Embedding model loaded.")
    return _EMBEDDINGS

def get_llm():
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=0.0,
        )
    elif LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=LLM_MODEL,
            temperature=0.0,
        )
    elif LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=LLM_MODEL,
            anthropic_api_key=ANTHROPIC_API_KEY,
            temperature=0.0,
        )
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0,
        )
    elif LLM_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=LLM_MODEL,
            temperature=0.0,
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
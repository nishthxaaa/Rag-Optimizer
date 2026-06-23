import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LLM_PROVIDER      = os.getenv("LLM_PROVIDER", "groq")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY    = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
HF_TOKEN          = os.getenv("HF_TOKEN", "")
LLM_MODEL         = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
CHROMA_PATH       = "chroma_db"

# ── Embeddings singleton ───────────────────────────────────────────────────────
_EMBEDDINGS = None

def get_embeddings():
    """
    Uses HuggingFace Inference API — zero local RAM, runs in the cloud.
    Model runs on HF servers, we just send text and get vectors back.
    """
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        print("[Config] Connecting to HuggingFace Inference API for embeddings...")
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        _EMBEDDINGS = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=HF_TOKEN,
        )
        print("[Config] HuggingFace embeddings ready.")
    return _EMBEDDINGS

# ── LLM ───────────────────────────────────────────────────────────────────────
def get_llm():
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=LLM_MODEL,
            temperature=0.0,
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=OPENAI_API_KEY,
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
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
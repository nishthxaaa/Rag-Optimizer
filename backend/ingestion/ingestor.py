import fitz  # PyMuPDF
import tiktoken
import chromadb
import uuid
from langchain_chroma import Chroma
from langchain_core.documents import Document
from backend.config import get_embeddings, CHROMA_PATH

CHUNK_CONFIGS = [
    {"chunk_size": 256,  "chunk_overlap": 30,  "name": "small"},
    {"chunk_size": 512,  "chunk_overlap": 50,  "name": "medium"},
    {"chunk_size": 1024, "chunk_overlap": 100, "name": "large"},
]
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file using PyMuPDF."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into chunks by token count with overlap."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start += chunk_size - chunk_overlap
        if start >= len(tokens):
            break
    return chunks

def ingest_document(pdf_path: str, doc_id: str) -> dict:
    print(f"[Ingestor] Extracting text from {pdf_path}...")
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        raise ValueError("Could not extract any text from this PDF.")
    
    print(f"[Ingestor] Extracted {len(raw_text)} characters.")
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embeddings = get_embeddings()  # Grab the Gemini embeddings from config!
    results = {}
    
    for config in CHUNK_CONFIGS:
        collection_name = f"{doc_id}_{config['name']}"
        print(f"[Ingestor] Creating collection '{collection_name}' (chunk_size={config['chunk_size']}, overlap={config['chunk_overlap']})...")
        
        # Wipe the old collection if it exists
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
            
        chunks = chunk_text(raw_text, config["chunk_size"], config["chunk_overlap"])
        
        # Convert raw text chunks into LangChain Document objects
        docs = []
        for i, chunk in enumerate(chunks):
            docs.append(Document(
                page_content=chunk, 
                metadata={"chunk_index": i, "config": config["name"]}
            ))
            
        # Add to ChromaDB using LangChain's wrapper so it uses Gemini embeddings
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            collection_name=collection_name,
            persist_directory=CHROMA_PATH
        )
        
        results[config["name"]] = {
            "collection_name": collection_name,
            "chunk_count": len(chunks),
            "chunk_size": config["chunk_size"],
            "chunk_overlap": config["chunk_overlap"],
        }
        
        print(f"[Ingestor]   -> {len(chunks)} chunks stored.")
        
    print(f"[Ingestor] Done. {len(CHUNK_CONFIGS)} collections created.")
    return results

if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else "test.pdf"
    doc_id = "test_doc"
    result = ingest_document(pdf, doc_id)
    print("\n=== Ingestion Summary ===")
    for name, info in result.items():
        print(f"  {name}: {info['chunk_count']} chunks in '{info['collection_name']}'")
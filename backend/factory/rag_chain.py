import chromadb
import time
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from backend.config import get_llm, get_embeddings, CHROMA_PATH

# The prompt template every RAG variant uses
RAG_PROMPT = ChatPromptTemplate.from_template("""
You are a precise assistant that answers questions strictly based on the provided context.
If the context does not contain enough information to answer, say "I don't have enough context to answer this."
Do not make up information.

Context:
{context}

Question:
{question}

Answer:
""")

def format_docs(docs) -> str:
    """Combine retrieved document chunks into a single context string."""
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

def build_rag_chain(collection_name: str, top_k: int = 4) -> dict:
    """
    Factory function — the core of the optimizer.
    
    Given a ChromaDB collection name and a top_k retrieval count,
    returns a fully working RAG chain + metadata about its config.
    
    Args:
        collection_name: e.g. "test_doc_medium"
        top_k: how many chunks to retrieve per query (3-6 is typical)
    
    Returns:
        {
            "chain": a LangChain runnable you can call with {"question": "..."},
            "retriever": the retriever (useful for debugging),
            "config": metadata dict describing this variant
        }
    """
    embeddings = get_embeddings()
    
    # Connect to the existing ChromaDB collection
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )
    
    # Build a retriever from this collection
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": top_k}
    )
    
    # Assemble the full RAG chain using LangChain's pipe syntax
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | get_llm()
        | StrOutputParser()
    )
    
    return {
        "chain": chain,
        "retriever": retriever,
        "config": {
            "collection_name": collection_name,
            "top_k": top_k,
        }
    }

def build_all_variants(doc_id: str) -> list[dict]:
    """
    Spawns all RAG variants for a given document.
    Each variant = different chunk config + different top_k value.
    Returns a list of variant dicts ready for evaluation.
    """
    from backend.ingestion.ingestor import CHUNK_CONFIGS
    
    variants = []
    
    # Test each chunk size with two different top_k values
    top_k_options = [3,6]
    
    for config in CHUNK_CONFIGS:
        for top_k in top_k_options:
            collection_name = f"{doc_id}_{config['name']}"
            variant = build_rag_chain(collection_name, top_k)
            
            # Enrich the config metadata
            variant["config"].update({
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                "chunk_name": config["name"],
                "variant_id": f"{config['name']}_k{top_k}",
            })
            
            variants.append(variant)
            print(f"[Factory] Built variant: {variant['config']['variant_id']}")
    
    print(f"[Factory] {len(variants)} variants ready.")
    return variants


if __name__ == "__main__":
    import sys
    
    # Quick test — run after Phase 1 test so ChromaDB collections exist
    # python -m backend.factory.rag_chain
    doc_id = sys.argv[1] if len(sys.argv) > 1 else "test_doc"
    
    print(f"Building variants for doc_id='{doc_id}'...")
    variants = build_all_variants(doc_id)
    
    # Ask all variants the same test question
    test_question = "What is this document about? Give a one sentence summary."
    
    print(f"\n=== Test Question: '{test_question}' ===\n")
    for v in variants:
        variant_id = v["config"]["variant_id"]
        print(f"[{variant_id}] Querying...")
        try:
            answer = v["chain"].invoke(test_question)
            print(f"[{variant_id}] Answer: {answer[:200]}...\n")
            
            
        except Exception as e:
            print(f"[{variant_id}] ERROR: {e}\n")
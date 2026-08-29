import os
from llama_index.llms.groq import Groq
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from utils import get_env


def setup_rag_pipeline(index, embed_model, top_k: int = None):
    if top_k is None:
        top_k = int(get_env("TOP_K", 3))  # Reduced from 5 to 3 for speed
    
    llm_model = get_env("LLM_MODEL", "llama-3.1-8b-instant")
    
    print(f"🔧 Setting up RAG with Groq model: {llm_model}")
    
    llm = Groq(
        model=llm_model,
        api_key=os.environ.get("GROQ_API_KEY"),
        temperature=0.1,
        max_tokens=512,  # Limit response length for speed
    )
    
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=top_k,
        embed_model=embed_model,
    )
    
    # Use "tree_summarize" for faster synthesis
    response_synthesizer = get_response_synthesizer(
        llm=llm,
        response_mode="tree_summarize",  # Faster than compact
    )
    
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )
    return query_engine, retriever


def query_with_sources(query_engine, retriever, query: str):
    """Retrieve nodes + generate answer, return both with metadata."""
    retrieved_nodes = retriever.retrieve(query)
    sources = []
    for node in retrieved_nodes:
        sources.append({
            "text": node.text[:200] + ("..." if len(node.text) > 200 else ""),
            "score": node.score,
            "file_name": node.metadata.get("file_name", "unknown"),
            "page": node.metadata.get("page_number", "unknown"),
        })
    
    response = query_engine.query(query)
    answer = str(response)
    return {
        "answer": answer,
        "sources": sources,
    }
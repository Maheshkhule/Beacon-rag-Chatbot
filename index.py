import os
import shutil
import pickle
from typing import List, Optional
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
import faiss
from utils import get_env


def chunk_documents(
    documents: List[Document],
    chunk_size: int = None,
    chunk_overlap: int = None
) -> List[TextNode]:
    if chunk_size is None:
        chunk_size = int(get_env("CHUNK_SIZE", 512))
    if chunk_overlap is None:
        chunk_overlap = int(get_env("CHUNK_OVERLAP", 100))
    
    print(f"✂️ Chunking {len(documents)} documents (size={chunk_size}, overlap={chunk_overlap})...")
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separator=" ",
        paragraph_separator="\n\n",
    )
    nodes = splitter.get_nodes_from_documents(documents)
    # Add extra metadata
    for node in nodes:
        node.metadata["chunk_id"] = node.node_id
        if "page_label" in node.metadata:
            node.metadata["page_number"] = node.metadata["page_label"]
        else:
            node.metadata["page_number"] = 0
    print(f"   → Created {len(nodes)} chunks.")
    return nodes


def build_index(nodes: List[TextNode], embed_model_name: str = None, persist_dir: str = None):
    if embed_model_name is None:
        embed_model_name = get_env("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    if persist_dir is None:
        persist_dir = get_env("STORAGE_FOLDER", "storage")
    
    print(f"🧠 Embedding {len(nodes)} chunks with '{embed_model_name}'...")
    embed_model = HuggingFaceEmbedding(model_name=embed_model_name)
    
    # FAISS index – HNSW for speed
    dimension = 384  # all-MiniLM-L6-v2 output
    faiss_index = faiss.IndexHNSWFlat(dimension, 32)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )
    
    # Persist the index and storage context
    os.makedirs(persist_dir, exist_ok=True)
    storage_context.persist(persist_dir=persist_dir)
    
    # Also save the index separately for faster loading
    faiss.write_index(faiss_index, os.path.join(persist_dir, "faiss.index"))
    
    print(f"   ✅ Index persisted to '{persist_dir}'.")
    return index, embed_model


def load_or_build_index(pdf_folder: str, storage_folder: str = None):
    if storage_folder is None:
        storage_folder = get_env("STORAGE_FOLDER", "storage")
    
    # Check if persisted index exists
    docstore_path = os.path.join(storage_folder, "docstore.json")
    faiss_path = os.path.join(storage_folder, "faiss.index")
    
    if os.path.exists(docstore_path) and os.path.exists(faiss_path):
        try:
            print(f"📂 Loading existing index from '{storage_folder}'...")
            embed_model = HuggingFaceEmbedding(model_name=get_env("EMBED_MODEL"))
            
            # Load FAISS index
            faiss_index = faiss.read_index(faiss_path)
            vector_store = FaissVectorStore(faiss_index=faiss_index)
            
            # Load storage context
            storage_context = StorageContext.from_defaults(
                persist_dir=storage_folder,
                vector_store=vector_store
            )
            
            # Load index
            index = load_index_from_storage(storage_context, embed_model=embed_model)
            print("   ✅ Index loaded successfully (no embedding needed).")
            return index, embed_model, None
            
        except Exception as e:
            print(f"⚠️ Error loading index: {e}")
            print("   🔄 Rebuilding index...")
            if os.path.exists(storage_folder):
                shutil.rmtree(storage_folder)
            # Continue to rebuild
    
    # Build from scratch
    print("🔄 Building index from scratch...")
    from ingestion import ingest_pdfs
    documents = ingest_pdfs(pdf_folder)
    nodes = chunk_documents(documents)
    index, embed_model = build_index(nodes, persist_dir=storage_folder)
    return index, embed_model, nodes
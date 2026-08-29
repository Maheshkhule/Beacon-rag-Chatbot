from index import load_or_build_index
from rag import setup_rag_pipeline, query_with_sources
from utils import get_env

if __name__ == "__main__":
    pdf_folder = get_env("PDF_FOLDER", "pdfs")
    print("🚀 Initializing RAG pipeline...")
    index, embed_model, _ = load_or_build_index(pdf_folder)
    query_engine, retriever = setup_rag_pipeline(index, embed_model)
    print("✅ Ready. Ask questions (type 'exit' to quit).")
    
    while True:
        q = input("\n❓ Your question: ")
        if q.lower() == "exit":
            break
        result = query_with_sources(query_engine, retriever, q)
        print("\n🤖 Answer:", result["answer"])
        print("\n📎 Sources:")
        for s in result["sources"]:
            print(f"  - {s['file_name']} (page {s['page']}) score: {s['score']:.4f}")
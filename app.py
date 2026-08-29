import streamlit as st
import os
import time
from datetime import datetime
from utils import get_env
from index import load_or_build_index
from rag import setup_rag_pipeline, query_with_sources

# Page configuration          (old)
st.set_page_config(
    page_title="Beacon- RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for ChatGPT-like UI
st.markdown("""
<style>
    /* Main container */
    .main {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        border-radius: 0.5rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    .user-message {
        background-color: #f0f4f8;
        border-radius: 1rem 1rem 0.25rem 1rem;
        margin-left: 2rem;
        padding: 0.75rem 1.25rem;
    }
    
    .assistant-message {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 1rem 1rem 1rem 0.25rem;
        margin-right: 2rem;
        padding: 0.75rem 1.25rem;
    }
    
    /* Avatar icons */
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin-right: 0.75rem;
        flex-shrink: 0;
    }
    
    .user-avatar {
        background-color: #10a37f;
        color: white;
    }
    
    .assistant-avatar {
        background-color: #5436da;
        color: white;
    }
    
    /* Sources section */
    .sources-container {
        background-color: #f9fafb;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin-top: 0.5rem;
        border-left: 3px solid #10a37f;
    }
    
    .source-item {
        padding: 0.25rem 0;
        font-size: 0.875rem;
        color: #4b5563;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .source-item:last-child {
        border-bottom: none;
    }
    
    .source-score {
        background-color: #dbeafe;
        padding: 0.1rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        color: #1e40af;
    }
    
    /* Response time */
    .response-time {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.5rem;
        font-style: italic;
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        border-radius: 0.5rem;
        border: 1px solid #d1d5db;
        padding: 0.75rem 1rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #10a37f;
        box-shadow: 0 0 0 2px rgba(16, 163, 127, 0.2);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Sidebar */
    .sidebar-content {
        padding: 1rem;
    }
    
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 1rem;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.5rem 1rem;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        background-color: #9ca3af;
        border-radius: 50%;
        animation: typingBounce 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typingBounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-6px); }
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d1d5db;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #9ca3af;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 Beacon - RAG Chatbot")
st.caption("Ask questions about your PDF collection — powered by Groq + FAISS")

# Load environment variables
pdf_folder = get_env("PDF_FOLDER", "pdfs")
if not os.path.exists(pdf_folder):
    st.error(f"📁 Folder '{pdf_folder}' not found. Please create it and place your PDFs inside.")
    st.stop()

# Cache the pipeline
@st.cache_resource
def get_pipeline():
    print("📂 Starting ingestion/indexing pipeline...")
    index, embed_model, _ = load_or_build_index(pdf_folder)
    print("🔧 Setting up RAG with Groq...")
    query_engine, retriever = setup_rag_pipeline(index, embed_model)
    print("🚀 Ready for queries!")
    return query_engine, retriever

# Load pipeline with spinner
with st.spinner("⏳ Loading your knowledge base..."):
    try:
        query_engine, retriever = get_pipeline()
    except Exception as e:
        st.error(f"❌ Error loading pipeline: {e}")
        st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # Add welcome message
    welcome_msg = """Hello! I'm your RAG chatbot. Ask me anything about the books in your collection.

📚 **Available books:**
- 12 Rules for Life
- A New Earth
- As a Man Thinketh
- Build the Life You Want
- Do What You Are
- Heal Yourself
- The Monk Who Sold His Ferrari
- The Power of Manifestation
- The Daily Stoic
- The Magic of Thinking Big
- Think and Grow Rich

💡 **Try asking:** *"What are the main principles of self-healing?"* or *"How does Stoicism help with daily challenges?"*"""
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_msg,
        "timestamp": datetime.now()
    })

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(
        message["role"],
        avatar="👤" if message["role"] == "user" else "🤖"
    ):
        st.markdown(message["content"])
        
        # Show timestamp for assistant messages
        if "timestamp" in message and message["role"] == "assistant":
            st.caption(f"🕐 {message['timestamp'].strftime('%I:%M %p')}")

# Chat input
if prompt := st.chat_input("Ask me anything about your books..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now()
    })
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("💭 Thinking..."):
            start_time = time.time()
            
            try:
                result = query_with_sources(query_engine, retriever, prompt)
                latency = time.time() - start_time
                
                answer = result["answer"]
                sources = result["sources"]
                
                # Display answer
                st.markdown(answer)
                
                # Display response time
                st.caption(f"⏱️ Response time: {latency:.2f} seconds")
                
                # Display sources in a nice expander
                if sources:
                    with st.expander("📎 **Sources**", expanded=False):
                        for i, src in enumerate(sources, 1):
                            st.markdown(f"""
                            <div class="source-item">
                                <strong>{i}.</strong> 📄 <strong>{src['file_name']}</strong> 
                                <span class="source-score">Page {src['page']}</span>
                                <span style="color: #6b7280; font-size: 0.8rem;">(Relevance: {src['score']:.3f})</span>
                                <br>
                                <span style="color: #4b5563; font-size: 0.85rem;">"{src['text']}"</span>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Save to session
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "timestamp": datetime.now()
                })
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I encountered an error: {str(e)}",
                    "timestamp": datetime.now()
                })

# Sidebar with info
with st.sidebar:
    st.markdown("""
    <div class="sidebar-content">
        <div class="sidebar-header">📊 System Info</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    - **Model:** `{get_env('LLM_MODEL', 'llama-3.1-8b-instant')}`
    - **Embeddings:** `all-MiniLM-L6-v2`
    - **Vector DB:** FAISS (HNSW)
    - **Retrieval:** Top-{get_env('TOP_K', 3)}
    - **Status:** ✅ Online
    """)
    
    st.divider()
    
    st.markdown("""
    **💡 Tips:**
    - Be specific with your questions
    - Ask about concepts across multiple books
    - Check sources for accuracy
    """)
    
    st.divider()
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
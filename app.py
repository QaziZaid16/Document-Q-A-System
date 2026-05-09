# ============================================================================
# app.py - Document Q&A Streamlit Application
# ============================================================================
# Purpose: Modern web UI for document question-answering using RAG pipeline.
#          Modeled after ChatGPT UX for familiar user experience.
#
# Architecture:
#   - Landing state: Upload-focused until document loaded
#   - Chat state: Full Q&A interface after document loaded
#   - Bottom input: File upload + text input in same row (ChatGPT style)
#
# ============================================================================

import streamlit as st
import tempfile
import os
from core.pdf_processor import process_pdf        
from core.embedder import build_or_load_index, retrieve_relevant_chunks 
from core.llm_handler import get_answer, check_ollama_status      

# ============================================================================
# PAGE CONFIGURATION & STYLING
# ============================================================================
print("[APP] Configuring Streamlit page...")
st.set_page_config(
    page_title="Document Q&A",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern ChatGPT-like appearance
st.markdown("""
<style>
    /* Main container centered with max width */
    .main {
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Chat styling */
    .chat-container {
        background: #fff;
        border-radius: 8px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

print("[APP] ✓ Page configured")

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
print("[APP] Initializing session state...")

if "index" not in st.session_state:
    st.session_state.index = None
    print("[APP] Initialized: index = None")

if "chunks" not in st.session_state:
    st.session_state.chunks = None
    print("[APP] Initialized: chunks = None")

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
    print("[APP] Initialized: pdf_name = None")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    print("[APP] Initialized: chat_history = []")

if "processing" not in st.session_state:
    st.session_state.processing = False
    print("[APP] Initialized: processing = False")

print("[APP] ✓ Session state ready")

# ============================================================================
# HEALTH CHECK
# ============================================================================
print("[APP] Checking Ollama status...")
ollama_healthy = check_ollama_status()
if not ollama_healthy:
    st.error(
        "⚠️ **Ollama not running**\n\n"
        "Please start Ollama first:\n"
        "```bash\nollama serve\n```"
    )
    st.stop()
print("[APP] ✓ Ollama healthy")

# ============================================================================
# LANDING STATE (Before upload)
# ============================================================================
if st.session_state.index is None:
    print("[APP] Showing landing state (no document loaded)")
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 📄 Document Q&A")
        st.markdown("### Chat with your PDFs")
        st.markdown("")

    # Feature highlight
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px; color: white;">
    
    ✨ **Smart Document Analysis**
    - Upload any PDF
    - Ask natural language questions
    - Get instant answers from your documents
    - See source citations
    
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Demo use case
    st.markdown("""
    **📋 Example Use Case:**
    
    *Retail Store Manager Workflow*
    1. Upload invoice PDF or product catalog
    2. Ask: "What was the total spend in Q1?"
    3. Get instant answer with source reference
    4. No more manual document scanning!
    """)

    st.markdown("---")

    # Upload section
    st.markdown("### 🚀 Get Started")
    
    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        help="Any PDF file - invoices, reports, documentation, etc.",
        key="landing_uploader"
    )
    
    if uploaded_file:
        print(f"[APP] File selected: {uploaded_file.name}")
        st.session_state.processing = True

        with st.spinner("⏳ Processing document... (extracting → embedding → indexing)"):
            try:
                print(f"[APP] Starting PDF processing pipeline for: {uploaded_file.name}")
                
                # Step 1: Save to temp
                print(f"[APP] Saving file to temporary location...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                print(f"[APP] ✓ Temp file: {tmp_path}")

                # Step 2: Process PDF
                print(f"[APP] Processing PDF...")
                chunks = process_pdf(tmp_path)
                print(f"[APP] ✓ PDF processed. {len(chunks)} chunks created")

                # Step 3: Build/load index
                print(f"[APP] Building/loading index...")
                index, chunks = build_or_load_index(
                    chunks,
                    index_path=f"index_{uploaded_file.name}"
                )
                print(f"[APP] ✓ Index ready")

                # Step 4: Save to session
                st.session_state.index = index
                st.session_state.chunks = chunks
                st.session_state.pdf_name = uploaded_file.name
                st.session_state.chat_history = []
                print(f"[APP] ✓ Session state updated")

                # Cleanup
                os.unlink(tmp_path)
                print(f"[APP] ✓ Temp file cleaned")

                st.session_state.processing = False
                st.success(f"✅ **{uploaded_file.name}** ready!\n\nStart asking questions →")
                st.rerun()

            except Exception as e:
                print(f"[APP] ❌ Error: {e}")
                st.session_state.processing = False
                st.error(f"❌ Error processing PDF: {str(e)}")

# ============================================================================
# CHAT STATE (After upload)
# ============================================================================
else:
    print("[APP] Showing chat interface")
    
    # Header with document info
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown("# 📄")
    with col2:
        st.markdown(f"### Chatting with: **{st.session_state.pdf_name}**")
        st.caption(f"📊 {len(st.session_state.chunks)} chunks | Ready to answer questions")
    with col3:
        if st.button("📁 Upload New", help="Upload a different PDF"):
            st.session_state.index = None
            st.session_state.chunks = None
            st.session_state.pdf_name = None
            st.session_state.chat_history = []
            print("[APP] Reset state for new upload")
            st.rerun()

    st.markdown("---")

    # Chat history
    chat_container = st.container()
    with chat_container:
        for i, exchange in enumerate(st.session_state.chat_history):
            # User message
            st.markdown(f"**You:** {exchange['question']}")
            
            # Assistant message
            st.markdown(f"**Assistant:** {exchange['answer']}")
            
            # Sources
            with st.expander("📚 View sources"):
                for j, chunk in enumerate(exchange['sources'], 1):
                    st.markdown(f"**Source {j}:**")
                    st.text(chunk[:300] + "..." if len(chunk) > 300 else chunk)
                    if j < len(exchange['sources']):
                        st.divider()
            
            st.divider()

    # Input area (ChatGPT style - bottom)
    st.markdown("---")
    
    # Input with upload button
    col1, col2 = st.columns([0.15, 0.85])
    
    with col1:
        st.markdown("### 📎")
        if st.button("📁", key="upload_new_btn", help="Upload different PDF"):
            st.session_state.index = None
            st.session_state.chunks = None
            st.session_state.pdf_name = None
            st.session_state.chat_history = []
            print("[APP] Reset for new document")
            st.rerun()
    
    with col2:
        # Use form to handle submission properly
        with st.form(key="question_form", clear_on_submit=True):
            question = st.text_input(
                "Ask a question about your document...",
                placeholder="e.g., What was the total amount? Who is the vendor?",
                label_visibility="collapsed"
            )
            submitted = st.form_submit_button("Send", use_container_width=True)

    # Process question only if form was submitted
    if submitted and question:
        print(f"[APP] Question submitted: {question[:60]}...")
        
        st.session_state.chat_history.append({
            "question": question,
            "answer": "⏳ Thinking...",
            "sources": []
        })
        
        # Show thinking
        with st.spinner("⏳ Processing question... (retrieving → generating answer)"):
            try:
                print(f"[APP] Retrieving relevant chunks...")
                # Dynamically set top_k: use min of (3, available chunks)
                top_k = min(3, len(st.session_state.chunks))
                relevant_chunks = retrieve_relevant_chunks(
                    query=question,
                    index=st.session_state.index,
                    chunks=st.session_state.chunks,
                    top_k=top_k
                )
                print(f"[APP] ✓ Retrieved {len(relevant_chunks)} chunks")

                print(f"[APP] Querying LLM...")
                result = get_answer(
                    question=question,
                    context_chunks=relevant_chunks
                )
                print(f"[APP] ✓ Got answer")

                # Update chat history
                st.session_state.chat_history[-1]["answer"] = result["answer"]
                st.session_state.chat_history[-1]["sources"] = result["sources"]
                print(f"[APP] ✓ Chat history updated")

            except Exception as e:
                print(f"[APP] ❌ Error: {e}")
                st.session_state.chat_history[-1]["answer"] = f"❌ Error: {str(e)}"

        st.rerun()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px; padding: 20px;">
🔐 Your documents are processed locally. No data sent to external servers.<br>
Powered by FAISS • SentenceTransformer • Ollama
</div>
""", unsafe_allow_html=True)

# ============================================================================
# ENTRY POINT FOR DIRECT PYTHON EXECUTION
# ============================================================================
if __name__ == "__main__":
    import subprocess
    import sys
    import os
    
    # Run Streamlit app when executed directly with `python app.py`
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__, "--logger.level=error"])
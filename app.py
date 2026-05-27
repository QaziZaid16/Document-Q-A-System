"""Streamlit Web Interface for Document Q&A System

This module provides the user-facing web interface for the RAG (Retrieval-Augmented
Generation) document Q&A system. It handles:
- PDF upload and processing
- User question input
- Answer retrieval and display
- Chat history management
"""

import streamlit as st
import tempfile
import os
from pdf_processor import process_pdf        
from embedder import build_or_load_index, retrieve_relevant_chunks 
from llm_handler import get_answer, check_ollama_status      

print("\n" + "="*70)
print("STREAMLIT APP INITIALIZED")
print("="*70)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

# Configure the Streamlit page with title, icon, and layout settings
st.set_page_config(
    page_title="Document Q&A",  
    page_icon="📄",            
    layout="wide"               
)
print("[DEBUG] Page configuration set")

# Inject custom CSS to create a sleek, minimal, dark UI without changing behavior
# Keep styles lightweight and resilient to Streamlit class name changes by targeting
# high-level elements and common IDs. This only affects appearance.
_custom_css = r"""
<style>
/* App background and global font color */
html, body, .stApp {
    background: #0b1115 !important;
    color: #e6eef2 !important;
}

/* Hide Streamlit default menu and footer for a cleaner demo look */
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;}

/* Make main content container slightly narrower and centered */
.block-container {
    padding-top: 1.2rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
}

/* Buttons and inputs: subtle rounded style */
button, .stButton>button {
    border-radius: 10px !important;
    background-color: #0ea5a1 !important;
    color: #051019 !important;
    border: none !important;
}

/* Chat card look for message containers (best-effort selectors) */
.stChatMessage, .stChatMessage>* {
    background: transparent !important;
}

/* A minimal centered header card */
.doc-card {
    max-width: 980px;
    margin: 0 auto 18px auto;
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.04);
    padding: 18px 20px;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(2,6,23,0.7);
}

/* Sidebar tweaks to make it compact */
.css-1d391kg { padding-top: 12px; }

</style>
"""
st.markdown(_custom_css, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Initialize session state variables that persist across reruns
# This allows data to survive when Streamlit reruns the script

if "index" not in st.session_state:
    st.session_state.index = None
    print("[DEBUG] Session: 'index' initialized to None")

if "chunks" not in st.session_state:
    st.session_state.chunks = None
    print("[DEBUG] Session: 'chunks' initialized to None")

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
    print("[DEBUG] Session: 'pdf_name' initialized to None")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    print("[DEBUG] Session: 'chat_history' initialized to empty list")

# ============================================================================
# MAIN PAGE TITLE AND INSTRUCTIONS
# ============================================================================

st.title("📄 Document Q&A")
st.caption("Upload a PDF and ask questions about its content. Answers are grounded in the document.")

# Small, centered header card to give a sleek, minimal landing appearance
_header_html = r"""
<div class="doc-card">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
        <div>
            <div style="font-size:18px;font-weight:600;color:#e6eef2">Document Q&A — Ask natural language questions about PDFs</div>
            <div style="margin-top:6px;color:#9fb4bf;font-size:13px">Upload a PDF (sidebar) and ask focused questions. Answers reference document passages.</div>
        </div>
        <div style="display:flex;gap:8px">
            <div style="background:#071018;color:#0ea5a1;padding:6px 10px;border-radius:8px;font-weight:600">Upload</div>
            <div style="background:transparent;border:1px solid rgba(255,255,255,0.04);color:#9fb4bf;padding:6px 10px;border-radius:8px">Interactive</div>
        </div>
    </div>
</div>
"""
st.markdown(_header_html, unsafe_allow_html=True)

# ============================================================================
# DEPENDENCY CHECK: ENSURE OLLAMA IS RUNNING
# ============================================================================

# Before proceeding, verify that Ollama LLM service is available
print("[DEBUG] Checking Ollama status...")
if not check_ollama_status():
    print("[WARNING] Ollama is not running!")
    st.warning(
        "⚠️ Ollama is not running. Start it with `ollama serve` in your terminal, "
        "then refresh this page."
    )
    st.stop()

print("[DEBUG] Ollama is running - proceeding with app")

# ============================================================================
# SIDEBAR: PDF UPLOAD AND PROCESSING
# ============================================================================

with st.sidebar:
    st.header("📂 Upload Document")
    print("[DEBUG] Rendering sidebar PDF upload section")

    uploaded_file = st.file_uploader(
        label="Choose a PDF file",
        type=["pdf"],   
        help="Upload the PDF document you want to query."
    )
    
    if uploaded_file is not None:
        print(f"[DEBUG] PDF file selected: {uploaded_file.name} ({uploaded_file.size} bytes)")
        st.success(f"✅ File: {uploaded_file.name}")
        size_kb = uploaded_file.size / 1024
        st.caption(f"Size: {size_kb:.1f} KB")
        
        # PROCESS PDF BUTTON
        # When clicked, this extracts text, cleans it, chunks it, embeds it, and builds a FAISS index
        if st.button("🔄 Process PDF", use_container_width=True):
            print(f"[DEBUG] Processing PDF: {uploaded_file.name}")
            with st.spinner("Processing PDF... this may take a minute."):
                # Create temporary file to store the uploaded PDF
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name
                print(f"[DEBUG] Temporary PDF saved to: {tmp_path}")
                
                # Step 1: Extract and process PDF into chunks
                print("[DEBUG] Calling process_pdf()...")
                chunks = process_pdf(tmp_path)
                print(f"[DEBUG] PDF processing complete: {len(chunks)} chunks created")
                
                # Step 2: Build or load FAISS index
                print("[DEBUG] Building/loading FAISS index...")
                index, chunks = build_or_load_index(
                    chunks,
                    index_path=f"index_{uploaded_file.name}"
                )
                print(f"[DEBUG] FAISS index ready with {len(chunks)} chunks")
                
                # Store results in session state (survives across reruns)
                st.session_state.index = index
                st.session_state.chunks = chunks
                st.session_state.pdf_name = uploaded_file.name
                st.session_state.chat_history = []  # Reset chat history for new PDF
                
                # Clean up temporary file
                os.unlink(tmp_path)
                print("[DEBUG] Temporary file deleted")

            st.success("✅ PDF processed! Ask your questions →")

    # Display current loaded PDF info
    if st.session_state.pdf_name:
        st.divider()
        print(f"[DEBUG] Current PDF loaded: {st.session_state.pdf_name}")
        st.caption(f"📄 Loaded: **{st.session_state.pdf_name}**")
        st.caption(f"📦 Chunks: {len(st.session_state.chunks)}")

    # ========================================================================
    # SIDEBAR: SETTINGS
    # ========================================================================
    
    st.divider()
    st.header("⚙️ Settings")
    
    # Control how many chunks are retrieved for each query
    top_k = st.slider(
        label="Chunks to retrieve",
        min_value=1,
        max_value=6,
        value=3,
        help="How many document chunks to send to the LLM. More = more context but slower."
    )
    print(f"[DEBUG] top_k setting: {top_k}")

# ============================================================================
# MAIN CONTENT AREA: CHAT INTERFACE
# ============================================================================

if st.session_state.index is None:
    # No PDF loaded yet - show instructions
    print("[DEBUG] No PDF loaded - showing startup message")
    st.info("👈 Upload and process a PDF from the sidebar to get started.")

else:
    print("[DEBUG] PDF loaded - rendering chat interface")
    
    # DISPLAY CHAT HISTORY
    # Shows all previous questions and answers from this session
    print(f"[DEBUG] Displaying {len(st.session_state.chat_history)} messages from chat history")
    for msg_idx, exchange in enumerate(st.session_state.chat_history):
        print(f"[DEBUG] Displaying message {msg_idx + 1}: {exchange['question'][:50]}...")
        
        # User message
        with st.chat_message("user"):
            st.write(exchange["question"])

        # Assistant message and source chunks
        with st.chat_message("assistant"):
            st.write(exchange["answer"])
            with st.expander("📚 View source chunks"):
                for i, chunk in enumerate(exchange["sources"]):
                    st.markdown(f"**Source {i+1}:**")
                    st.text(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                    if i < len(exchange["sources"]) - 1:
                        st.divider()

    # INPUT: USER QUESTION
    # Chat input field that triggers on Enter or custom submit
    question = st.chat_input("Ask a question about your document...")

    if question:
        print(f"[DEBUG] User question submitted: {question[:50]}...")
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(question)

        # Process question and display answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                print(f"[DEBUG] Retrieving relevant chunks (top_k={top_k})...")
                
                # STEP 1: RETRIEVAL - Find most relevant chunks using FAISS
                relevant_chunks = retrieve_relevant_chunks(
                    query=question,
                    index=st.session_state.index,
                    chunks=st.session_state.chunks,
                    top_k=top_k   
                )
                print(f"[DEBUG] Retrieved {len(relevant_chunks)} relevant chunks")
                
                # STEP 2: GENERATION - Send context + question to LLM
                print("[DEBUG] Sending to LLM for answer generation...")
                result = get_answer(
                    question=question,
                    context_chunks=relevant_chunks
                )
                print(f"[DEBUG] LLM answer generated: {len(result['answer'])} characters")

            # Display the generated answer
            st.write(result["answer"])

            # Show which chunks were used (source attribution)
            with st.expander("📚 View source chunks"):
                for i, chunk in enumerate(result["sources"]):
                    st.markdown(f"**Source {i+1}:**")
                    st.text(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                    if i < len(result["sources"]) - 1:
                        st.divider()

        # Save to chat history for this session
        st.session_state.chat_history.append({
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"]
        })
        print(f"[DEBUG] Message saved to chat history (total: {len(st.session_state.chat_history)})")

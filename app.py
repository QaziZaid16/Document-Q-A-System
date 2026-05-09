# ============================================================================
# app.py - Streamlit Web Interface for Document Q&A
# ============================================================================
# Purpose: Main user-facing application using Streamlit framework.
#          Provides UI for uploading PDFs and asking questions about them.
# 
# Architecture:
#   - Sidebar: File upload & settings
#   - Main: Chat interface with source attribution
#
# Flow:
#   1. User uploads PDF
#   2. App processes PDF → creates embeddings → builds FAISS index
#   3. User asks question
#   4. App retrieves relevant chunks → queries LLM → displays answer + sources
# ============================================================================

import streamlit as st
import tempfile
import os
from pdf_processor import process_pdf        
from embedder import build_or_load_index, retrieve_relevant_chunks 
from llm_handler import get_answer, check_ollama_status      

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
print("[APP] Configuring Streamlit page...")
st.set_page_config(
    page_title="Document Q&A",      # Browser tab title
    page_icon="📄",                 # Browser tab icon
    layout="wide"                   # Wide layout for better use of space
)
print("[APP] ✓ Page configured")

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
# Streamlit reruns the script on every interaction, so we use session_state
# to persist data across reruns
print("[APP] Initializing session state...")

if "index" not in st.session_state:
    st.session_state.index = None  # FAISS index
    print("[APP] Initialized: index = None")

if "chunks" not in st.session_state:
    st.session_state.chunks = None  # Original text chunks
    print("[APP] Initialized: chunks = None")

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None  # Name of loaded PDF
    print("[APP] Initialized: pdf_name = None")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Previous Q&A exchanges
    print("[APP] Initialized: chat_history = []")

print("[APP] ✓ Session state ready")

# ============================================================================
# HEADER & INTRO
# ============================================================================
st.title("📄 Document Q&A")
st.caption("Upload a PDF and ask questions about its content. Answers are grounded in the document.")

# ============================================================================
# HEALTH CHECK: Verify Ollama is running
# ============================================================================
print("[APP] Checking Ollama status...")
if not check_ollama_status():
    print("[APP] ❌ Ollama not running!")
    st.warning(
        "⚠️ Ollama is not running. Start it with `ollama serve` in your terminal, "
        "then refresh this page."
    )
    st.stop()  # Stop execution here
print("[APP] ✓ Ollama is running")

# ============================================================================
# SIDEBAR: FILE UPLOAD & SETTINGS
# ============================================================================
with st.sidebar:
    st.header("📂 Upload Document")
    
    # File uploader widget
    uploaded_file = st.file_uploader(
        label="Choose a PDF file",
        type=["pdf"],
        help="Upload the PDF document you want to query."
    )
    
    # Process uploaded file if user selected one
    if uploaded_file is not None:
        st.success(f"✅ File: {uploaded_file.name}")
        size_kb = uploaded_file.size / 1024
        st.caption(f"Size: {size_kb:.1f} KB")
        
        if st.button("🔄 Process PDF", use_container_width=True):
            print(f"[APP] User clicked 'Process PDF' for: {uploaded_file.name}")
            
            with st.spinner("Processing PDF... this may take a minute."):
                try:
                    # === STEP 1: Write uploaded file to temp location ===
                    print(f"[APP] Saving uploaded file to temporary location...")
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        tmp_path = tmp_file.name
                    print(f"[APP] ✓ Temp file created: {tmp_path}")
                    
                    # === STEP 2: Process PDF (extract, clean, chunk) ===
                    print(f"[APP] Starting PDF processing pipeline...")
                    chunks = process_pdf(tmp_path)
                    print(f"[APP] ✓ PDF processing complete. {len(chunks)} chunks created")
                    
                    # === STEP 3: Build/load FAISS index ===
                    print(f"[APP] Building or loading FAISS index...")
                    index, chunks = build_or_load_index(
                        chunks,
                        index_path=f"index_{uploaded_file.name}"
                    )
                    print(f"[APP] ✓ FAISS index ready with {len(chunks)} chunks")
                    
                    # === STEP 4: Save to session state ===
                    st.session_state.index = index
                    st.session_state.chunks = chunks
                    st.session_state.pdf_name = uploaded_file.name
                    st.session_state.chat_history = []  # Reset chat for new PDF
                    print(f"[APP] ✓ Session state updated")
                    
                    # === STEP 5: Clean up temp file ===
                    os.unlink(tmp_path)
                    print(f"[APP] ✓ Temp file cleaned up")
                    
                    st.success("✅ PDF processed! Ask your questions →")
                    
                except Exception as e:
                    print(f"[APP] ❌ Error processing PDF: {e}")
                    st.error(f"Error processing PDF: {str(e)}")

    # Show current document status if one is loaded
    if st.session_state.pdf_name:
        st.divider()
        st.caption(f"📖 Loaded: **{st.session_state.pdf_name}**")
        st.caption(f"📦 Chunks: {len(st.session_state.chunks)}")

    # ========================================================================
    # SETTINGS PANEL
    # ========================================================================
    st.divider()
    st.header("⚙️ Settings")
    top_k = st.slider(
        label="Chunks to retrieve",
        min_value=1,
        max_value=6,
        value=3,
        help="How many document chunks to send to the LLM. More = more context but slower."
    )
    print(f"[APP] Retrieved setting: top_k = {top_k}")

# ============================================================================
# MAIN CONTENT AREA: CHAT INTERFACE
# ============================================================================

# Show info message if no PDF is loaded
if st.session_state.index is None:
    print("[APP] No PDF loaded, showing welcome message")
    st.info("👈 Upload and process a PDF from the sidebar to get started.")

else:
    # === DISPLAY CHAT HISTORY ===
    print(f"[APP] Displaying chat history with {len(st.session_state.chat_history)} messages")
    for exchange in st.session_state.chat_history:
        # Display user message
        with st.chat_message("user"):
            st.write(exchange["question"])

        # Display assistant response with sources
        with st.chat_message("assistant"):
            st.write(exchange["answer"])
            with st.expander("📚 View source chunks"):
                for i, chunk in enumerate(exchange["sources"]):
                    st.markdown(f"**Source {i+1}:**")
                    # Show first 400 chars of chunk with ellipsis
                    st.text(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                    if i < len(exchange["sources"]) - 1:
                        st.divider()

    # === CHAT INPUT ===
    question = st.chat_input("Ask a question about your document...")

    if question:
        print(f"[APP] User question: {question[:100]}...")
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(question)

        # Process question and display response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # === STEP 1: Retrieve relevant chunks from FAISS ===
                    print(f"[APP] Retrieving {top_k} relevant chunks...")
                    relevant_chunks = retrieve_relevant_chunks(
                        query=question,
                        index=st.session_state.index,
                        chunks=st.session_state.chunks,
                        top_k=top_k   
                    )
                    print(f"[APP] ✓ Retrieved {len(relevant_chunks)} chunks")

                    # === STEP 2: Query LLM with context ===
                    print(f"[APP] Querying LLM...")
                    result = get_answer(
                        question=question,
                        context_chunks=relevant_chunks
                    )
                    print(f"[APP] ✓ Got LLM response")

                    # === STEP 3: Display answer ===
                    st.write(result["answer"])

                    # === STEP 4: Display source attribution ===
                    with st.expander("📚 View source chunks"):
                        for i, chunk in enumerate(result["sources"]):
                            st.markdown(f"**Source {i+1}:**")
                            st.text(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                            if i < len(result["sources"]) - 1:
                                st.divider()
                    
                    print(f"[APP] ✓ Response displayed")
                    
                except Exception as e:
                    print(f"[APP] ❌ Error getting answer: {e}")
                    st.error(f"Error getting answer: {str(e)}")
                    result = None

        # Add exchange to chat history if successful
        if result:
            st.session_state.chat_history.append({
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"]
            })
            print(f"[APP] ✓ Added exchange to chat history")
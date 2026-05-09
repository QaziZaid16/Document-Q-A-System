# app.py

import streamlit as st
import tempfile
import os
from pdf_processor import process_pdf        
from embedder import build_or_load_index, retrieve_relevant_chunks 
from llm_handler import get_answer, check_ollama_status      

st.set_page_config(
    page_title="Document Q&A",  
    page_icon="📄",            
    layout="wide"               
                                
)

if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("📄 Document Q&A")
st.caption("Upload a PDF and ask questions about its content. Answers are grounded in the document.")

if not check_ollama_status():
    st.warning(
        "⚠️ Ollama is not running. Start it with `ollama serve` in your terminal, "
        "then refresh this page."
    )
    st.stop()

with st.sidebar:
    st.header("📂 Upload Document")

    uploaded_file = st.file_uploader(
        label="Choose a PDF file",
        type=["pdf"],   
        help="Upload the PDF document you want to query."
    )
    if uploaded_file is not None:
        st.success(f"✅ File: {uploaded_file.name}")
        size_kb = uploaded_file.size / 1024
        st.caption(f"Size: {size_kb:.1f} KB")
        if st.button("🔄 Process PDF", use_container_width=True):
            with st.spinner("Processing PDF... this may take a minute."):
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name
                chunks = process_pdf(tmp_path)
                index, chunks = build_or_load_index(
                    chunks,
                    index_path=f"index_{uploaded_file.name}"
                )
                st.session_state.index = index
                st.session_state.chunks = chunks
                st.session_state.pdf_name = uploaded_file.name
                st.session_state.chat_history = []
                os.unlink(tmp_path)

            st.success("✅ PDF processed! Ask your questions →")

    if st.session_state.pdf_name:
        st.divider()
        st.caption(f"📖 Loaded: **{st.session_state.pdf_name}**")
        st.caption(f"📦 Chunks: {len(st.session_state.chunks)}")

    st.divider()
    st.header("⚙️ Settings")
    top_k = st.slider(
        label="Chunks to retrieve",
        min_value=1,
        max_value=6,
        value=3,
        help="How many document chunks to send to the LLM. More = more context but slower."
    )

if st.session_state.index is None:
    st.info("👈 Upload and process a PDF from the sidebar to get started.")

else:
    for exchange in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(exchange["question"])

        with st.chat_message("assistant"):
            st.write(exchange["answer"])
            with st.expander("📚 View source chunks"):
                for i, chunk in enumerate(exchange["sources"]):
                    st.markdown(f"**Source {i+1}:**")
                    st.text(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                    if i < len(exchange["sources"]) - 1:
                        st.divider()

    question = st.chat_input("Ask a question about your document...")

    if question:

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                relevant_chunks = retrieve_relevant_chunks(
                    query=question,
                    index=st.session_state.index,
                    chunks=st.session_state.chunks,
                    top_k=top_k   
                )

                result = get_answer(
                    question=question,
                    context_chunks=relevant_chunks
                )

            st.write(result["answer"])

            with st.expander("📚 View source chunks"):
                for i, chunk in enumerate(result["sources"]):
                    st.markdown(f"**Source {i+1}:**")
                    st.text(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                    if i < len(result["sources"]) - 1:
                        st.divider()

        st.session_state.chat_history.append({
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"]
        })
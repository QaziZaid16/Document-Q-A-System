# 📄 Document Q&A System

A local, privacy-first document question-answering system built with RAG (Retrieval-Augmented Generation). Upload any PDF and ask questions about it — answers are grounded strictly in the document's content, with no external APIs involved.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![FAISS](https://img.shields.io/badge/Search-FAISS-orange)
![Ollama](https://img.shields.io/badge/LLM-Ollama-green)

---

## ✨ Features

- **100% local** — no OpenAI, no API keys, no data leaves your machine
- **Semantic search** — understands meaning, not just keywords
- **Source transparency** — every answer shows the exact document chunks it came from
- **Multi-turn chat** — ask follow-up questions with conversation history
- **Adjustable retrieval** — tune how many chunks to retrieve via a sidebar slider

---

## 🏗️ How It Works (RAG Pipeline)

```
PDF Upload → Extract Text → Chunk → Embed → FAISS Index
                                                  ↓
                          Answer ← Local LLM ← Retrieve Top-K Chunks ← User Question
```

The system uses **Retrieval-Augmented Generation (RAG)**:

1. **Indexing** (once per PDF)
   - Extract raw text using PyMuPDF
   - Split into overlapping 500-word chunks (50-word overlap to preserve context at boundaries)
   - Convert each chunk into a 384-dimensional semantic vector using `all-MiniLM-L6-v2`
   - Store vectors in a FAISS index for fast nearest-neighbor search

2. **Querying** (every question)
   - Embed the user's question using the same model
   - Find the top-K most semantically similar chunks via FAISS
   - Build a grounded prompt: context chunks + question + strict instructions
   - Send to a local LLM (Ollama) and return the answer

---

## 🗂️ Project Structure

```
document-qa/
│
├── app.py              # Streamlit UI — entry point
├── pdf_processor.py    # Part 1: PDF text extraction and chunking
├── embedder.py         # Part 2: Sentence embeddings and FAISS index
├── llm_handler.py      # Part 3: Prompt building and Ollama integration
│
├── requirements.txt    # Python dependencies
└── README.md
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.9 or higher
- [Ollama](https://ollama.ai) installed on your machine

### 1. Clone the repository

```bash
git clone https://github.com/your-username/document-qa.git
cd document-qa
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~90 MB) on first run. It caches locally and works offline after that.

### 3. Install and start Ollama

```bash
# Install Ollama (macOS / Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the LLM (downloads ~4 GB — do this once)
ollama pull llama3

# Start the Ollama server (keep this terminal open)
ollama serve
```

> **Low-spec machine?** Use `phi3` instead — only ~2 GB and still great for Q&A:
> ```bash
> ollama pull phi3
> ```
> Then change `MODEL_NAME = "phi3"` in `llm_handler.py`.

### 4. Run the app

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

---

## 🚀 Usage

1. Open the app in your browser
2. Upload a PDF using the sidebar
3. Click **Process PDF** and wait for indexing to complete
4. Type your question in the chat box and press Enter
5. Expand **View source chunks** under any answer to see exactly where it came from

---

## 🛠️ Tech Stack

| Component | Library | Purpose |
|-----------|---------|---------|
| UI | Streamlit | Web interface |
| PDF parsing | PyMuPDF (`fitz`) | Extract text from PDF pages |
| Embeddings | `sentence-transformers` | Convert text to semantic vectors |
| Vector search | FAISS (`faiss-cpu`) | Fast nearest-neighbor retrieval |
| Local LLM | Ollama + llama3 | Answer generation |

---

## 🔧 Configuration

All key parameters are tunable:

| Parameter | Where | Default | Effect |
|-----------|-------|---------|--------|
| Chunk size | `pdf_processor.py` | 500 words | Larger = more context per chunk |
| Overlap | `pdf_processor.py` | 50 words | Less context lost at boundaries |
| Top-K chunks | Sidebar slider | 3 | More chunks = richer context, slower LLM |
| LLM model | `llm_handler.py` | `llama3` | Swap for `mistral`, `phi3`, etc. |
| Temperature | `llm_handler.py` | 0.1 | Lower = more deterministic answers |

---

## ⚠️ Limitations

- **Scanned PDFs** — image-only PDFs have no text layer; PyMuPDF returns empty strings. Fix: add OCR via `pytesseract`.
- **Very large PDFs** — embedding thousands of chunks takes time on CPU. Fix: use a GPU or smaller chunk size.
- **LLM context window** — if retrieved chunks are very long, they may exceed the local model's context limit. Fix: reduce chunk size or top-K.
- **Answer quality** — bounded by the local model's capability. `llama3` is strong; smaller models may struggle with complex reasoning.

---

## 💡 Design Decisions

**Why overlapping chunks?**
A sentence at the boundary of two chunks should appear in both, so its context is never lost during retrieval.

**Why `all-MiniLM-L6-v2`?**
It hits the sweet spot — fast enough for real-time CPU use, small enough to run locally, and accurate enough for production RAG. It produces 384-dimensional vectors trained on over 1 billion sentence pairs.

**Why FAISS over Pinecone or Chroma?**
FAISS runs entirely in-process with no server required. For document-scale data (hundreds to low thousands of chunks), `IndexFlatL2` (exact search) is both fast enough and simpler to reason about.

**Why Ollama over HuggingFace `transformers` directly?**
Ollama handles model quantization, memory management, and serving automatically. Swap models with one command, no GPU memory management code needed.

---

## 📋 requirements.txt

```
streamlit
pymupdf
sentence-transformers
faiss-cpu
numpy
requests
```
# Document-Q-A-System

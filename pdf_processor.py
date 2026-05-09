"""PDF Processing Module

This module handles the extraction, cleaning, and chunking of text from PDF documents.
It's the first step in the RAG (Retrieval-Augmented Generation) pipeline.
"""

import fitz
import re
from typing import List

# ============================================================================
# STEP 1: PDF TEXT EXTRACTION
# ============================================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file, page by page.
    
    This function opens a PDF, iterates through each page, and collects all
    the text content. Pages are joined with newlines to preserve structure.
    
    Args:
        pdf_path: Path to the PDF file to extract text from
        
    Returns:
        A single string containing all text from the PDF
    """
    print(f"  \n[DEBUG] extract_text_from_pdf() called with: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    all_text = []
    print(f"  [DEBUG] PDF opened successfully. Total pages: {doc.page_count}")

    for page_num, page in enumerate(doc):
        text_page = page.get_text()
        all_text.append(text_page)
        print(f"  [DEBUG] Page {page_num + 1}: {len(text_page)} characters extracted")

    doc.close()
    print(f"  [DEBUG] PDF closed")

    full_text = "\n".join(all_text)
    print(f"  [DEBUG] Total extracted text: {len(full_text)} characters")
    return full_text

# ============================================================================
# STEP 2: TEXT CLEANING
# ============================================================================

def clean_text(text: str) -> str:
    """Normalize whitespace and remove leading/trailing spaces.
    
    This function:
    - Replaces multiple consecutive whitespace characters with a single space
    - Removes leading and trailing whitespace
    
    This cleaning step prevents redundant spacing that can affect chunking.
    
    Args:
        text: The raw text to clean
        
    Returns:
        The cleaned text with normalized whitespace
    """
    print(f"  \n[DEBUG] clean_text() called")
    print(f"  [DEBUG] Input text length: {len(text)} characters")
    
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()  # Remove leading/trailing whitespace
    
    print(f"  [DEBUG] After cleaning: {len(text)} characters")
    return text

# ============================================================================
# STEP 3: TEXT CHUNKING
# ============================================================================

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for embedding and retrieval.
    
    Breaking text into chunks allows:
    - Efficient embedding (smaller vectors)
    - Better semantic retrieval (specific passages instead of whole document)
    - Overlap between chunks preserves context and prevents important info from
      being split across boundaries
    
    Example: If chunk_size=500 and overlap=50:
      Chunk 1: words[0:500]
      Chunk 2: words[450:950]  (50 word overlap)
      Chunk 3: words[900:1400] (50 word overlap)
    
    Args:
        text: The cleaned text to chunk
        chunk_size: Number of words per chunk (default 500)
        overlap: Number of overlapping words between chunks (default 50)
        
    Returns:
        A list of text chunks as strings
    """
    print(f"  \n[DEBUG] chunk_text() called")
    print(f"  [DEBUG] Parameters: chunk_size={chunk_size}, overlap={overlap}")
    
    words = text.split()
    print(f"  [DEBUG] Total words: {len(words)}")
    
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)
        print(f"  [DEBUG] Chunk {len(chunks)}: words {start}-{end} ({len(chunk_words)} words)")

        start += chunk_size - overlap

    print(f"  [DEBUG] Total chunks created: {len(chunks)}")
    return chunks

# ============================================================================
# MASTER FUNCTION: ORCHESTRATE ALL STEPS
# ============================================================================

def process_pdf(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Master function that orchestrates the complete PDF processing pipeline.
    
    This is the main entry point. It combines all three steps:
    1. Extract text from PDF
    2. Clean and normalize the text
    3. Split into overlapping chunks
    
    Args:
        pdf_path: Path to the PDF file
        chunk_size: Number of words per chunk (default 500)
        overlap: Number of overlapping words between chunks (default 50)
        
    Returns:
        A list of text chunks ready for embedding and retrieval
    """
    print(f"\n{'='*70}")
    print(f"PDF PROCESSING STARTED")
    print(f"File: {pdf_path}")
    print(f"{'='*70}")
    
    print(f"\n[1/3] Extracting text from PDF...")
    raw_text = extract_text_from_pdf(pdf_path)

    print(f"\n[2/3] Cleaning text...")
    clean = clean_text(raw_text)

    print(f"\n[3/3] Chunking into pieces of {chunk_size} words with {overlap} word overlap...")
    chunks = chunk_text(clean, chunk_size=chunk_size, overlap=overlap)

    print(f"\n{'='*70}")
    print(f"PDF PROCESSING COMPLETE")
    print(f"Result: {len(chunks)} chunks from {len(clean.split())} total words")
    print(f"Average chunk size: {len(clean.split()) // len(chunks)} words")
    print(f"{'='*70}\n")
    
    return chunks
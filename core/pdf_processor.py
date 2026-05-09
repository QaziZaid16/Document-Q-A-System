"""
pdf_processor.py
================
Purpose: Extract text from PDF files, clean it, and split into overlapping chunks.
This is the first stage of the RAG (Retrieval Augmented Generation) pipeline.
Used by: app.py as the first step when processing uploaded documents.
"""

import fitz  # PyMuPDF library for reading PDFs
import re
from typing import List
import os


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    STAGE 1: Extract all text from a PDF file.
    
    Purpose: Opens a PDF and extracts raw text from every page, preserving
             page breaks to maintain document structure.
    
    Args:
        pdf_path (str): Path to the PDF file to read
        
    Returns:
        str: All extracted text with newlines between pages
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If file is not a valid PDF
    """
    # === INPUT VALIDATION ===
    print(f"[PDF Processor] Validating PDF file: {pdf_path}")
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"File must be a PDF. Got: {pdf_path}")
    
    try:
        # === OPEN PDF ===
        print(f"[PDF Processor] Opening PDF document...")
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"[PDF Processor] ✓ PDF opened successfully. Total pages: {total_pages}")
        
        # === EXTRACT TEXT FROM EACH PAGE ===
        all_text = []
        for page_num, page in enumerate(doc, 1):
            text_page = page.get_text()
            all_text.append(text_page)
            if page_num % max(1, total_pages // 5) == 0 or page_num == total_pages:
                print(f"[PDF Processor]   Extracted {page_num}/{total_pages} pages...")
        
        # === CLOSE DOCUMENT ===
        doc.close()
        print(f"[PDF Processor] ✓ Extraction complete. {len(all_text)} pages processed.")
        
        # === COMBINE PAGES WITH SEPARATORS ===
        full_text = "\n".join(all_text)
        print(f"[PDF Processor] Total characters extracted: {len(full_text)}")
        return full_text
        
    except fitz.FileError as e:
        raise ValueError(f"Invalid PDF file or corrupted: {e}")
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {e}")


def clean_text(text: str) -> str:
    """
    STAGE 2: Clean and normalize extracted text.
    
    Purpose: Removes extra whitespace, tabs, newlines to standardize text
             format. This prevents chunking issues and improves embedding quality.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned and normalized text
        
    Raises:
        TypeError: If input is not a string
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text)}")
    
    print(f"[PDF Processor] Cleaning text...")
    original_len = len(text)
    
    # === REMOVE MULTIPLE WHITESPACES ===
    # Replace multiple spaces, tabs, newlines with single space
    text = re.sub(r'\s+', ' ', text)
    print(f"[PDF Processor] Collapsed whitespace")
    
    # === STRIP LEADING/TRAILING WHITESPACE ===
    text = text.strip()
    print(f"[PDF Processor] ✓ Cleaned: {original_len} → {len(text)} characters")
    
    if len(text) == 0:
        raise ValueError("Cleaned text is empty. PDF may not contain readable text.")
    
    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    STAGE 3: Split text into overlapping chunks for embedding.
    
    Purpose: Creates overlapping text chunks so the embedding/retrieval model
             can match queries to relevant document sections. Overlap ensures
             important information isn't cut off between chunks.
    
    Example: chunk_size=500, overlap=50
             Chunk 1: words[0:500]
             Chunk 2: words[450:950]  (overlap of 50)
             Chunk 3: words[900:1400] (overlap of 50)
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Target words per chunk (default: 500)
        overlap (int): Words to repeat between chunks (default: 50)
        
    Returns:
        List[str]: List of text chunks
        
    Raises:
        ValueError: If invalid chunk parameters
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text)}")
    
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(f"overlap must be in range [0, {chunk_size}), got {overlap}")
    
    print(f"[PDF Processor] Chunking text (size: {chunk_size} words, overlap: {overlap} words)...")
    
    # === SPLIT INTO WORDS ===
    words = text.split()
    total_words = len(words)
    print(f"[PDF Processor] Total words: {total_words}")
    
    chunks = []
    start = 0
    
    # === CREATE OVERLAPPING CHUNKS ===
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)
        
        # Move start position, accounting for overlap
        start += chunk_size - overlap
    
    print(f"[PDF Processor] ✓ Created {len(chunks)} chunks from {total_words} words")
    
    # Debug: show chunk size distribution
    avg_chunk_size = total_words / len(chunks) if chunks else 0
    print(f"[PDF Processor] Average words per chunk: {avg_chunk_size:.1f}")
    
    return chunks


def process_pdf(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    MASTER FUNCTION: Orchestrate the complete PDF processing pipeline.
    
    Purpose: Combines all three stages (extract → clean → chunk) into one
             convenient function. This is what app.py calls directly.
    
    Pipeline:
        1. Extract text from PDF file
        2. Clean and normalize the text
        3. Split into overlapping chunks
    
    Args:
        pdf_path (str): Path to PDF file
        chunk_size (int): Words per chunk (default: 500)
        overlap (int): Overlapping words between chunks (default: 50)
        
    Returns:
        List[str]: List of text chunks ready for embedding
        
    Raises:
        FileNotFoundError: If PDF not found
        ValueError: If PDF is invalid or text cannot be extracted
    """
    print("\n" + "="*60)
    print("📄 PDF PROCESSING PIPELINE")
    print("="*60)
    
    try:
        # === STAGE 1: EXTRACT ===
        print(f"\n[1/3] Extracting text from PDF...")
        raw_text = extract_text_from_pdf(pdf_path)
        
        # === STAGE 2: CLEAN ===
        print(f"\n[2/3] Cleaning text...")
        clean = clean_text(raw_text)
        
        # === STAGE 3: CHUNK ===
        print(f"\n[3/3] Chunking into pieces...")
        chunks = chunk_text(clean, chunk_size=chunk_size, overlap=overlap)
        
        # === SUMMARY ===
        print("\n" + "="*60)
        print("✅ PDF PROCESSING COMPLETE")
        print("="*60)
        print(f"📊 Summary:")
        print(f"   • Total chunks created: {len(chunks)}")
        print(f"   • Total words processed: {len(clean.split())}")
        print(f"   • Average chunk size: {len(clean.split()) / len(chunks):.1f} words")
        print("="*60 + "\n")
        
        return chunks
        
    except Exception as e:
        print(f"\n❌ PDF PROCESSING FAILED: {e}")
        print("="*60 + "\n")
        raise

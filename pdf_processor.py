import fitz
import re
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    all_text = []

    for page in doc:
        text_page = page.get_text()
        all_text.append(text_page)

    doc.close()

    full_text = "\n".join(all_text)
    return full_text

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

def process_pdf(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:

    print(f"[1/3] Extracting text from PDF...")
    raw_text = extract_text_from_pdf(pdf_path)

    print(f"[2/3] Cleaning text...")
    clean = clean_text(raw_text)

    print(f"[3/3] Chunking into pieces of {chunk_size} words with {overlap} word overlap...")
    chunks = chunk_text(clean, chunk_size=chunk_size, overlap=overlap)

    print(f"Done. Created {len(chunks)} chunks from {len(clean.split())} total words.")
    return chunks
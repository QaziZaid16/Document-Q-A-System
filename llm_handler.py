# llm_handler.py

import requests

import json

from typing import List

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL_NAME = "llama3"

def format_prompt(question: str, context_chunks: List[str]) -> str:
    """
    Builds the full prompt string we'll send to the LLM.
    This is the core of RAG — we're injecting the retrieved context
    directly into the prompt so the LLM reads it before answering.

    question:       the user's raw question string
    context_chunks: list of relevant text chunks from FAISS retrieval

    Returns: a single formatted string — the complete prompt
    """
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""You are a helpful assistant that answers questions based strictly on the provided document context.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

    return prompt

def query_ollama(prompt: str, temperature: float = 0.1) -> str:

    payload = {
        "model": MODEL_NAME,   
        "prompt": prompt,       
        "stream": False,        
                               
        "options": {
            "temperature": temperature,

            "num_predict": 512,
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,     
                                
            timeout=120         
        )

        response.raise_for_status()

        result = response.json()
        return result["response"].strip()

    except requests.exceptions.ConnectionError:
       
        return "Error: Could not connect to Ollama. Make sure Ollama is running (run 'ollama serve' in terminal)."

    except requests.exceptions.Timeout:
        return "Error: The model took too long to respond. Try a smaller model like 'phi3'."

    except KeyError:
        return f"Error: Unexpected response format from Ollama: {result}"
    
def get_answer(question: str, context_chunks: List[str]) -> dict:
    """
    The single function the rest of the app calls.
    Combines prompt formatting + LLM querying into one clean call.

    Returns a dict with both the answer AND the source chunks —
    so the UI can show "here's the answer, and here's where it came from."
    Showing sources is important for trust and debuggability.

    Returns: {
        "answer": "the LLM's response",
        "sources": ["chunk text 1", "chunk text 2", ...]
    }
    """

    prompt = format_prompt(question, context_chunks)
    word_count = len(prompt.split())
    print(f"Sending prompt to LLM ({word_count} words ≈ {int(word_count / 0.75)} tokens)")

    answer = query_ollama(prompt)

    return {
        "answer": answer,
        "sources": context_chunks   
    }

def check_ollama_status() -> bool:
    """
    Quick health check — is Ollama running?
    Call this on app startup so we fail fast with a clear message
    instead of crashing mid-conversation.

    Returns: True if Ollama is up, False otherwise
    """
    try:
        # Ollama exposes a root endpoint that returns basic info
        response = requests.get("http://localhost:11434", timeout=3)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


# --- Optional: list available models ---
def list_available_models() -> List[str]:
    """
    Asks Ollama which models are installed on this machine.
    Useful for letting the user pick a model in the UI.
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        data = response.json()
        # Ollama returns {"models": [{"name": "llama3:latest", ...}, ...]}
        return [m["name"] for m in data.get("models", [])]
    except:
        return []   
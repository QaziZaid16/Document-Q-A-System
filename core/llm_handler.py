"""
llm_handler.py - LLM Interface & Prompt Management
================================================
Purpose: Query the Ollama LLM with context from retrieved documents.
         This is the final step of the RAG pipeline.

Architecture:
  - format_prompt: Inject context into a structured prompt template
  - query_ollama: Send prompt to LLM and get response
  - get_answer: Orchestrate the full pipeline
"""

import requests
import json
from typing import List

# ============================================================================
# CONFIGURATION
# ============================================================================
print("[LLM Handler] Configuring LLM handler...")

OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint
MODEL_NAME = "llama3"  # Which model to use (must be installed in Ollama)

print(f"[LLM Handler] Ollama URL: {OLLAMA_URL}")
print(f"[LLM Handler] Model: {MODEL_NAME}")


# ============================================================================
# PROMPT FORMATTING
# ============================================================================

def format_prompt(question: str, context_chunks: List[str]) -> str:
    """
    STEP 1: Build the complete prompt for the LLM.
    
    Purpose: This is the core of RAG (Retrieval Augmented Generation).
             We inject the retrieved document context directly into the prompt
             so the LLM reads relevant information before answering.
    
    Prompt structure:
      [System instruction] → [Document context] → [User question] → [Answer]
    
    Args:
        question (str): User's question
        context_chunks (List[str]): Retrieved document chunks
        
    Returns:
        str: Complete formatted prompt ready for LLM
        
    Raises:
        ValueError: If question or chunks are empty
    """
    # === INPUT VALIDATION ===
    if not isinstance(question, str) or len(question.strip()) == 0:
        raise ValueError("Question cannot be empty")
    
    if not context_chunks or len(context_chunks) == 0:
        raise ValueError("Must provide at least one context chunk")
    
    print(f"[LLM Handler] Formatting prompt with {len(context_chunks)} context chunks...")
    
    # === JOIN CONTEXT CHUNKS ===
    # Add separator between chunks so LLM can distinguish them
    context = "\n\n---\n\n".join(context_chunks)
    total_context_words = len(context.split())
    print(f"[LLM Handler] Total context: {total_context_words} words")
    
    # === BUILD PROMPT ===
    # Use a structured format so the LLM understands what to do
    prompt = f"""You are a helpful assistant that answers questions based strictly on the provided document context.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""

    print(f"[LLM Handler] ✓ Prompt formatted ({len(prompt)} chars)")
    return prompt


# ============================================================================
# LLM QUERYING
# ============================================================================

def query_ollama(prompt: str, temperature: float = 0.1) -> str:
    """
    STEP 2: Send prompt to Ollama LLM and get response.
    
    Purpose: Calls the local Ollama API with the formatted prompt.
             Uses low temperature (0.1) for consistent, factual answers.
    
    Args:
        prompt (str): Formatted prompt with context
        temperature (float): Creativity level (0.0=factual, 1.0=creative)
                           Default 0.1 keeps answers grounded in context
        
    Returns:
        str: LLM's response text
        
    Raises:
        ConnectionError: If Ollama not running
        TimeoutError: If LLM takes too long
    """
    # === BUILD REQUEST ===
    payload = {
        "model": MODEL_NAME,           # Which model to use
        "prompt": prompt,              # The complete prompt
        "stream": False,               # Wait for complete response (not streaming)
        "options": {
            "temperature": temperature,  # Lower = more factual
            "num_predict": 512,         # Max tokens in response
        }
    }
    
    print(f"[LLM Handler] 🧠 Querying Ollama ({MODEL_NAME})...")
    print(f"[LLM Handler] Temperature: {temperature}, Max tokens: 512")
    
    try:
        # === SEND REQUEST ===
        print(f"[LLM Handler] Sending request to {OLLAMA_URL}...")
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120  # 2 minute timeout
        )
        
        # === CHECK FOR ERRORS ===
        response.raise_for_status()
        print(f"[LLM Handler] ✓ Response received (status: {response.status_code})")
        
        # === EXTRACT RESPONSE ===
        result = response.json()
        answer = result["response"].strip()
        print(f"[LLM Handler] ✓ Answer retrieved ({len(answer)} chars)")
        
        return answer

    except requests.exceptions.ConnectionError as e:
        error_msg = "Error: Could not connect to Ollama. Make sure Ollama is running (run 'ollama serve' in terminal)."
        print(f"[LLM Handler] ❌ Connection error: {e}")
        return error_msg

    except requests.exceptions.Timeout as e:
        error_msg = "Error: The model took too long to respond. Try a smaller model like 'phi3'."
        print(f"[LLM Handler] ❌ Timeout error: {e}")
        return error_msg

    except requests.exceptions.RequestException as e:
        error_msg = f"Error: Request failed: {str(e)}"
        print(f"[LLM Handler] ❌ Request error: {e}")
        return error_msg

    except KeyError as e:
        error_msg = f"Error: Unexpected response format from Ollama: {result}"
        print(f"[LLM Handler] ❌ KeyError parsing response: {e}")
        return error_msg
    
    except Exception as e:
        error_msg = f"Error: Unexpected error: {str(e)}"
        print(f"[LLM Handler] ❌ Unexpected error: {e}")
        return error_msg

    
# ============================================================================
# ORCHESTRATION
# ============================================================================

def get_answer(question: str, context_chunks: List[str]) -> dict:
    """
    MASTER FUNCTION: Get LLM answer with context + source attribution.
    
    Purpose: This is what the UI calls. Combines formatting + querying 
             in one convenient function. Returns both answer and sources
             so UI can show where the answer came from.
    
    Args:
        question (str): User's question
        context_chunks (List[str]): Retrieved document chunks
        
    Returns:
        dict with keys:
          - "answer": str - the LLM's response
          - "sources": List[str] - the context chunks used
          
    Raises:
        ValueError: If question or chunks empty
    """
    # === INPUT VALIDATION ===
    if not isinstance(question, str) or len(question.strip()) == 0:
        raise ValueError("Question cannot be empty")
    
    if not context_chunks or len(context_chunks) == 0:
        raise ValueError("Must provide at least one context chunk")
    
    print(f"\n[LLM Handler] Getting answer for: '{question[:60]}...'")
    
    try:
        # === STEP 1: FORMAT PROMPT ===
        prompt = format_prompt(question, context_chunks)
        word_count = len(prompt.split())
        print(f"[LLM Handler] Prompt size: {word_count} words (≈{int(word_count / 0.75)} tokens)")

        # === STEP 2: QUERY LLM ===
        answer = query_ollama(prompt)
        
        # === STEP 3: RETURN WITH ATTRIBUTION ===
        print(f"[LLM Handler] ✓ Answer ready")
        
        return {
            "answer": answer,
            "sources": context_chunks  # UI will show these
        }
        
    except Exception as e:
        print(f"[LLM Handler] ❌ Error in get_answer: {e}")
        return {
            "answer": f"Error: {str(e)}",
            "sources": context_chunks
        }


# ============================================================================
# HEALTH CHECKS
# ============================================================================

def check_ollama_status() -> bool:
    """
    HEALTH CHECK: Is Ollama running and accessible?
    
    Purpose: Quick check on app startup so we fail fast with clear message
             instead of crashing mid-conversation.
    
    Returns:
        bool: True if Ollama is up and responding
    """
    print("[LLM Handler] Checking Ollama health...")
    
    try:
        # Ollama exposes a root endpoint that returns basic info
        response = requests.get("http://localhost:11434", timeout=3)
        is_healthy = response.status_code == 200
        
        if is_healthy:
            print("[LLM Handler] ✓ Ollama is healthy and running")
        else:
            print(f"[LLM Handler] ❌ Ollama returned status {response.status_code}")
        
        return is_healthy
        
    except requests.exceptions.ConnectionError:
        print("[LLM Handler] ❌ Could not connect to Ollama")
        return False
    except Exception as e:
        print(f"[LLM Handler] ❌ Health check failed: {e}")
        return False


# ============================================================================
# UTILITY: List Available Models
# ============================================================================

def list_available_models() -> List[str]:
    """
    UTILITY: List all models installed in Ollama.
    
    Purpose: Useful for letting users pick a model in the UI.
             Also helps debug if expected model isn't installed.
    
    Returns:
        List[str]: List of model names (e.g., ["llama3:latest", "phi3:latest"])
                   Empty list if Ollama unavailable
    """
    print("[LLM Handler] Querying available models...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        # Ollama returns: {"models": [{"name": "llama3:latest", ...}, ...]}
        models = [m["name"] for m in data.get("models", [])]
        
        print(f"[LLM Handler] ✓ Found {len(models)} models: {models}")
        return models
        
    except Exception as e:
        print(f"[LLM Handler] ❌ Error listing models: {e}")
        return []

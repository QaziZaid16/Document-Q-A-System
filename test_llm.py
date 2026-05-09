# test_llm.py — run this to verify Part 3 works independently

from llm_handler import get_answer, check_ollama_status

if not check_ollama_status():
    print("Ollama is not running! Run 'ollama serve' in a terminal first.")
    exit()

fake_chunks = [
    "The mitochondria is the powerhouse of the cell. It produces ATP through a process called oxidative phosphorylation. This requires oxygen and glucose as inputs.",
    "ATP stands for Adenosine Triphosphate. It is the primary energy currency of the cell. Every cellular process that requires energy uses ATP.",
    "Without mitochondria, cells cannot produce sufficient energy and will die. Red blood cells are one of the few cell types that lack mitochondria."
]

result = get_answer("What does the mitochondria produce?", fake_chunks)
print("ANSWER:", result["answer"])
print("\nSOURCE CHUNKS USED:")
for i, chunk in enumerate(result["sources"]):
    print(f"  [{i+1}] {chunk[:100]}...")

result2 = get_answer("What is the capital of France?", fake_chunks)
print("\n\nOUT-OF-CONTEXT ANSWER:", result2["answer"])
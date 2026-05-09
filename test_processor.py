from pdf_processor import process_pdf

chunks = process_pdf("your_document.pdf")

print(f"Total chunks: {len(chunks)}")
print(f"\nFirst chunk preview:\n{chunks[0][:300]}...")
print(f"\nLast chunk preview:\n{chunks[-1][:300]}...")

words_0 = chunks[0].split()
words_1 = chunks[1].split()
print(f"\nLast 5 words of chunk 0: {words_0[-5:]}")
print(f"First 5 words of chunk 1: {words_1[:5]}")
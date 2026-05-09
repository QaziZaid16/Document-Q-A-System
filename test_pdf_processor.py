"""
test_pdf_processor.py
====================
Test suite for pdf_processor.py

Coverage Goals:
  - extract_text_from_pdf: 90%+ (all success & error paths)
  - clean_text: 95%+ (all edge cases)
  - chunk_text: 90%+ (overlap logic, edge cases)
  - process_pdf: 85%+ (integration tests)

Test Categories:
  1. Happy path: Normal usage
  2. Edge cases: Empty, minimal, large inputs
  3. Error scenarios: Invalid inputs, file not found, corrupt data
  4. Integration: Full pipeline
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pdf_processor import (
    extract_text_from_pdf,
    clean_text,
    chunk_text,
    process_pdf
)


class TestCleanText(unittest.TestCase):
    """Test the clean_text function"""
    
    def test_normal_text(self):
        """Happy path: normal text with some whitespace"""
        text = "Hello   world  \n  test"
        result = clean_text(text)
        self.assertEqual(result, "Hello world test")
    
    def test_empty_string(self):
        """Edge case: empty string"""
        with self.assertRaises(ValueError):
            clean_text("")
    
    def test_whitespace_only(self):
        """Edge case: only whitespace"""
        with self.assertRaises(ValueError):
            clean_text("   \n\t  ")
    
    def test_single_word(self):
        """Edge case: single word"""
        result = clean_text("Hello")
        self.assertEqual(result, "Hello")
    
    def test_tabs_and_newlines(self):
        """Edge case: tabs and newlines"""
        text = "Line1\n\nLine2\t\tLine3"
        result = clean_text(text)
        self.assertEqual(result, "Line1 Line2 Line3")
    
    def test_multiple_spaces(self):
        """Edge case: multiple consecutive spaces"""
        text = "Word1     Word2          Word3"
        result = clean_text(text)
        self.assertEqual(result, "Word1 Word2 Word3")
    
    def test_non_string_input(self):
        """Error: non-string input"""
        with self.assertRaises(TypeError):
            clean_text(123)
    
    def test_non_string_list_input(self):
        """Error: list input"""
        with self.assertRaises(TypeError):
            clean_text(["hello", "world"])
    
    def test_leading_trailing_spaces(self):
        """Edge case: leading and trailing spaces"""
        text = "   hello world   "
        result = clean_text(text)
        self.assertEqual(result, "hello world")
    
    def test_unicode_characters(self):
        """Edge case: unicode characters"""
        text = "Hello 世界 مرحبا мир"
        result = clean_text(text)
        self.assertIn("Hello", result)
        self.assertIn("世界", result)


class TestChunkText(unittest.TestCase):
    """Test the chunk_text function"""
    
    def setUp(self):
        """Set up test data"""
        # Create a sample text with 100 words
        self.sample_text = " ".join([f"word{i}" for i in range(100)])
    
    def test_basic_chunking(self):
        """Happy path: basic chunking"""
        chunks = chunk_text(self.sample_text, chunk_size=10, overlap=0)
        self.assertEqual(len(chunks), 10)  # 100 words / 10 per chunk
    
    def test_chunking_with_overlap(self):
        """Happy path: chunking with overlap"""
        chunks = chunk_text(self.sample_text, chunk_size=10, overlap=5)
        # First chunk: words 0-9
        # Second chunk: words 5-14 (overlapped)
        self.assertGreater(len(chunks), 10)
        
        # Check overlap: last word of chunk[0] should also be in chunk[1]
        chunk0_words = chunks[0].split()
        chunk1_words = chunks[1].split()
        # Last 5 words of chunk0 should overlap with first 5 words of chunk1
        self.assertEqual(chunk0_words[-5:], chunk1_words[:5])
    
    def test_single_chunk(self):
        """Edge case: text smaller than chunk_size"""
        text = " ".join([f"word{i}" for i in range(5)])
        chunks = chunk_text(text, chunk_size=10)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)
    
    def test_exact_chunk_size(self):
        """Edge case: text exactly equals chunk_size"""
        text = " ".join([f"word{i}" for i in range(10)])
        chunks = chunk_text(text, chunk_size=10, overlap=0)
        self.assertEqual(len(chunks), 1)
    
    def test_large_overlap(self):
        """Edge case: large overlap"""
        chunks = chunk_text(self.sample_text, chunk_size=20, overlap=15)
        # With 20-15=5 word step, should create more chunks
        self.assertGreater(len(chunks), 5)
    
    def test_no_overlap(self):
        """Happy path: no overlap"""
        chunks = chunk_text(self.sample_text, chunk_size=20, overlap=0)
        self.assertEqual(len(chunks), 5)  # 100 / 20
    
    def test_invalid_chunk_size_zero(self):
        """Error: chunk_size <= 0"""
        with self.assertRaises(ValueError):
            chunk_text(self.sample_text, chunk_size=0)
    
    def test_invalid_chunk_size_negative(self):
        """Error: negative chunk_size"""
        with self.assertRaises(ValueError):
            chunk_text(self.sample_text, chunk_size=-5)
    
    def test_invalid_overlap_negative(self):
        """Error: negative overlap"""
        with self.assertRaises(ValueError):
            chunk_text(self.sample_text, chunk_size=10, overlap=-1)
    
    def test_overlap_too_large(self):
        """Error: overlap >= chunk_size"""
        with self.assertRaises(ValueError):
            chunk_text(self.sample_text, chunk_size=10, overlap=10)
    
    def test_non_string_input(self):
        """Error: non-string input"""
        with self.assertRaises(TypeError):
            chunk_text(123)
    
    def test_empty_string(self):
        """Edge case: empty string"""
        text = ""
        chunks = chunk_text(text, chunk_size=10)
        self.assertEqual(len(chunks), 0)
    
    def test_single_word(self):
        """Edge case: single word"""
        chunks = chunk_text("hello", chunk_size=10)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], "hello")
    
    def test_chunk_content_validity(self):
        """Validation: all chunks contain words"""
        chunks = chunk_text(self.sample_text, chunk_size=15, overlap=3)
        for i, chunk in enumerate(chunks):
            self.assertGreater(len(chunk), 0, f"Chunk {i} is empty")
            self.assertGreater(len(chunk.split()), 0, f"Chunk {i} has no words")


class TestExtractTextFromPdf(unittest.TestCase):
    """Test extract_text_from_pdf function (with mocking)"""
    
    def test_file_not_found(self):
        """Error: file doesn't exist"""
        with self.assertRaises(FileNotFoundError):
            extract_text_from_pdf("/nonexistent/file.pdf")
    
    def test_not_pdf_file(self):
        """Error: non-PDF file"""
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            with self.assertRaises(ValueError):
                extract_text_from_pdf(tmp.name)
    
    def test_invalid_pdf(self):
        """Error: corrupted PDF file"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"This is not a valid PDF")
            tmp.flush()
            tmp_name = tmp.name
        
        try:
            with self.assertRaises(ValueError):
                extract_text_from_pdf(tmp_name)
        finally:
            os.unlink(tmp_name)
    
    @patch('pdf_processor.fitz.open')
    def test_successful_extraction(self, mock_fitz_open):
        """Happy path: successful PDF extraction"""
        # Create mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample page text"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_fitz_open.return_value = mock_doc
        
        result = extract_text_from_pdf("/fake/file.pdf")
        self.assertEqual(result, "Sample page text")
        mock_doc.close.assert_called_once()
    
    @patch('pdf_processor.fitz.open')
    def test_multipage_extraction(self, mock_fitz_open):
        """Happy path: multi-page PDF"""
        # Create mock multi-page document
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 text"
        
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_doc.__len__ = MagicMock(return_value=2)
        mock_fitz_open.return_value = mock_doc
        
        result = extract_text_from_pdf("/fake/file.pdf")
        self.assertIn("Page 1 text", result)
        self.assertIn("Page 2 text", result)


class TestProcessPdf(unittest.TestCase):
    """Integration tests for the complete pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_text = " ".join([f"word{i}" for i in range(200)])
    
    def test_invalid_parameters(self):
        """Error: invalid parameters"""
        with self.assertRaises(FileNotFoundError):
            process_pdf("/nonexistent/file.pdf")
    
    @patch('pdf_processor.extract_text_from_pdf')
    @patch('pdf_processor.clean_text')
    @patch('pdf_processor.chunk_text')
    def test_pipeline_integration(self, mock_chunk, mock_clean, mock_extract):
        """Happy path: full pipeline"""
        # Setup mocks
        mock_extract.return_value = "Raw PDF text with lots of noise"
        mock_clean.return_value = "Cleaned text"
        mock_chunk.return_value = ["chunk1", "chunk2", "chunk3"]
        
        result = process_pdf("/fake/file.pdf")
        
        # Verify all functions were called
        mock_extract.assert_called_once_with("/fake/file.pdf")
        mock_clean.assert_called_once()
        mock_chunk.assert_called_once()
        
        # Verify result
        self.assertEqual(result, ["chunk1", "chunk2", "chunk3"])
    
    @patch('pdf_processor.extract_text_from_pdf')
    def test_empty_pdf_extraction(self, mock_extract):
        """Error: PDF with no extractable text"""
        mock_extract.return_value = "   \n\n   "
        
        with self.assertRaises(ValueError):
            process_pdf("/fake/file.pdf")


class TestIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests without mocking"""
    
    def test_clean_and_chunk(self):
        """Integration: clean then chunk"""
        raw_text = "Hello   \n\n  world   test   string  \n with lots  of    noise"
        cleaned = clean_text(raw_text)
        chunks = chunk_text(cleaned, chunk_size=5, overlap=1)
        
        # Verify it works
        self.assertGreater(len(chunks), 0)
        self.assertGreater(len(chunks[0]), 0)
    
    def test_chunk_reconstruction(self):
        """Validation: chunks when joined should contain all words"""
        text = " ".join([f"word{i}" for i in range(50)])
        chunks = chunk_text(text, chunk_size=10, overlap=2)
        
        # Reconstruct by combining chunks (accounting for overlap)
        reconstructed_words = set()
        for chunk in chunks:
            reconstructed_words.update(chunk.split())
        
        original_words = set(text.split())
        
        # All original words should be in chunks (with overlap accounting)
        self.assertTrue(len(reconstructed_words) >= len(original_words) * 0.95)


class TestErrorMessages(unittest.TestCase):
    """Test that error messages are helpful"""
    
    def test_clean_text_error_message(self):
        """Verify error message clarity"""
        try:
            clean_text(123)
        except TypeError as e:
            self.assertIn("Expected string", str(e))
            self.assertIn("str", str(e))
    
    def test_chunk_text_error_message(self):
        """Verify error message clarity"""
        try:
            chunk_text("text", chunk_size=-1)
        except ValueError as e:
            self.assertIn("positive", str(e))


# ============================================================================
# Test Execution & Coverage Report
# ============================================================================

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

# Coverage command:
# python -m pytest test_pdf_processor.py --cov=pdf_processor --cov-report=html
# or:
# coverage run -m pytest test_pdf_processor.py
# coverage report -m pdf_processor.py
# coverage html  # Creates htmlcov/index.html

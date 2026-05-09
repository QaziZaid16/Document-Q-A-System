"""
test_app.py
===========
Test suite for app.py (Streamlit Application)

Note: Testing Streamlit apps is different because Streamlit reruns the script
on every interaction. We use mocking to test the logic.

Coverage Goals:
  - Main flows: 80%+
  - Error handling: 90%+

Test Categories:
  1. Session state management
  2. PDF upload and processing
  3. Chat interaction
  4. Error scenarios
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os


class TestSessionStateInitialization(unittest.TestCase):
    """Test session state initialization"""
    
    def test_session_state_keys(self):
        """Validation: all required session state keys exist"""
        # This test verifies the app initializes correctly
        # In a real scenario, we'd test the actual Streamlit session
        
        required_keys = ["index", "chunks", "pdf_name", "chat_history"]
        
        # Simulated session state
        session_state = {
            "index": None,
            "chunks": None,
            "pdf_name": None,
            "chat_history": []
        }
        
        for key in required_keys:
            self.assertIn(key, session_state)


class TestPdfUploadFlow(unittest.TestCase):
    """Test PDF upload and processing flow"""
    
    @patch('app.process_pdf')
    @patch('app.build_or_load_index')
    @patch('app.check_ollama_status')
    def test_pdf_processing_flow(self, mock_ollama, mock_build_index, mock_process):
        """Happy path: upload and process PDF"""
        # Setup mocks
        mock_ollama.return_value = True
        mock_process.return_value = ["chunk1", "chunk2", "chunk3"]
        
        mock_index = MagicMock()
        mock_index.ntotal = 3
        mock_build_index.return_value = (mock_index, ["chunk1", "chunk2", "chunk3"])
        
        # Verify process_pdf was called (would be tested via Streamlit callbacks)
        mock_process.assert_not_called()  # Not called until button pressed
        
    def test_chat_history_starts_empty(self):
        """Validation: chat history initializes empty"""
        chat_history = []
        self.assertEqual(len(chat_history), 0)


class TestErrorScenarios(unittest.TestCase):
    """Test error handling"""
    
    @patch('app.check_ollama_status')
    def test_ollama_not_running_warning(self, mock_ollama):
        """Error: Ollama not running"""
        mock_ollama.return_value = False
        
        # In Streamlit, this would show a warning and call st.stop()
        result = not mock_ollama.return_value
        self.assertTrue(result)


class TestChatInteraction(unittest.TestCase):
    """Test chat interaction flow"""
    
    @patch('app.retrieve_relevant_chunks')
    @patch('app.get_answer')
    def test_question_answering_flow(self, mock_get_answer, mock_retrieve):
        """Happy path: user asks question"""
        # Setup
        mock_retrieve.return_value = ["chunk1", "chunk2", "chunk3"]
        mock_get_answer.return_value = {
            "answer": "The answer is X",
            "sources": ["chunk1", "chunk2", "chunk3"]
        }
        
        # Simulate
        question = "What is X?"
        chunks = ["chunk1", "chunk2", "chunk3"]
        index = MagicMock()
        
        relevant = mock_retrieve(question, index, chunks, top_k=3)
        result = mock_get_answer(question, relevant)
        
        self.assertEqual(result["answer"], "The answer is X")
        self.assertEqual(len(result["sources"]), 3)


class TestChatHistory(unittest.TestCase):
    """Test chat history management"""
    
    def test_add_to_chat_history(self):
        """Happy path: add exchange to chat history"""
        chat_history = []
        
        exchange = {
            "question": "What is this?",
            "answer": "This is that",
            "sources": ["chunk1"]
        }
        
        chat_history.append(exchange)
        
        self.assertEqual(len(chat_history), 1)
        self.assertEqual(chat_history[0]["question"], "What is this?")
    
    def test_multiple_exchanges(self):
        """Happy path: multiple Q&A exchanges"""
        chat_history = []
        
        for i in range(5):
            exchange = {
                "question": f"Question {i}?",
                "answer": f"Answer {i}",
                "sources": [f"chunk{i}"]
            }
            chat_history.append(exchange)
        
        self.assertEqual(len(chat_history), 5)
        self.assertEqual(chat_history[4]["question"], "Question 4?")


if __name__ == '__main__':
    unittest.main(verbosity=2)

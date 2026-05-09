"""
test_llm_handler.py
===================
Test suite for llm_handler.py

Coverage Goals:
  - format_prompt: 95%+
  - query_ollama: 90%+
  - get_answer: 90%+
  - check_ollama_status: 95%+
  - list_available_models: 90%+

Test Categories:
  1. Happy path: Normal usage
  2. Edge cases: Empty inputs, special characters
  3. Error scenarios: Connection errors, timeouts, malformed responses
  4. Error handling: Verify graceful degradation
"""

import unittest
from unittest.mock import patch, MagicMock
import requests

from llm_handler import (
    format_prompt,
    query_ollama,
    get_answer,
    check_ollama_status,
    list_available_models,
    OLLAMA_URL,
    MODEL_NAME
)


class TestFormatPrompt(unittest.TestCase):
    """Test the format_prompt function"""
    
    def test_normal_prompt(self):
        """Happy path: format normal prompt"""
        question = "What is the capital of France?"
        chunks = ["France is a country in Europe", "Paris is the capital of France"]
        
        result = format_prompt(question, chunks)
        
        self.assertIn(question, result)
        self.assertIn(chunks[0], result)
        self.assertIn(chunks[1], result)
        self.assertIn("CONTEXT:", result)
        self.assertIn("QUESTION:", result)
        self.assertIn("ANSWER:", result)
    
    def test_single_chunk(self):
        """Edge case: single chunk"""
        question = "What is this?"
        chunks = ["Some context about something"]
        
        result = format_prompt(question, chunks)
        
        self.assertIn(question, result)
        self.assertIn(chunks[0], result)
    
    def test_many_chunks(self):
        """Edge case: many chunks"""
        question = "What?"
        chunks = [f"Chunk {i}" for i in range(10)]
        
        result = format_prompt(question, chunks)
        
        self.assertIn(question, result)
        for chunk in chunks:
            self.assertIn(chunk, result)
    
    def test_empty_question(self):
        """Error: empty question"""
        with self.assertRaises(ValueError):
            format_prompt("", ["context"])
    
    def test_whitespace_only_question(self):
        """Error: whitespace-only question"""
        with self.assertRaises(ValueError):
            format_prompt("   \n\t  ", ["context"])
    
    def test_empty_chunks(self):
        """Error: empty chunks list"""
        with self.assertRaises(ValueError):
            format_prompt("What?", [])
    
    def test_none_chunks(self):
        """Error: None chunks"""
        with self.assertRaises(ValueError):
            format_prompt("What?", None)
    
    def test_special_characters(self):
        """Edge case: special characters in question"""
        question = "What is 2+2? How about €100?"
        chunks = ["Context with émoji 😀"]
        
        result = format_prompt(question, chunks)
        self.assertIn(question, result)
        self.assertIn(chunks[0], result)
    
    def test_very_long_question(self):
        """Edge case: very long question"""
        question = "What is " + "very " * 100 + "long?"
        chunks = ["context"]
        
        result = format_prompt(question, chunks)
        self.assertIn(question, result)
    
    def test_very_long_context(self):
        """Edge case: very long context"""
        question = "What?"
        chunks = [" ".join([f"word{i}" for i in range(1000)])]
        
        result = format_prompt(question, chunks)
        self.assertIn(question, result)
        self.assertGreater(len(result), 5000)


class TestQueryOllama(unittest.TestCase):
    """Test the query_ollama function"""
    
    @patch('llm_handler.requests.post')
    def test_successful_response(self, mock_post):
        """Happy path: successful LLM response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "The answer is 42"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = query_ollama("Test prompt")
        
        self.assertEqual(result, "The answer is 42")
        mock_post.assert_called_once()
    
    @patch('llm_handler.requests.post')
    def test_connection_error(self, mock_post):
        """Error: connection error"""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        result = query_ollama("Test prompt")
        
        self.assertIn("Error", result)
        self.assertIn("Could not connect", result)
    
    @patch('llm_handler.requests.post')
    def test_timeout_error(self, mock_post):
        """Error: timeout"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = query_ollama("Test prompt")
        
        self.assertIn("Error", result)
        self.assertIn("took too long", result)
    
    @patch('llm_handler.requests.post')
    def test_http_error(self, mock_post):
        """Error: HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_post.return_value = mock_response
        
        result = query_ollama("Test prompt")
        
        self.assertIn("Error", result)
    
    @patch('llm_handler.requests.post')
    def test_malformed_response(self, mock_post):
        """Error: malformed JSON response"""
        mock_response = MagicMock()
        mock_response.json.side_effect = KeyError("response")
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = query_ollama("Test prompt")
        
        self.assertIn("Error", result)
        self.assertIn("Unexpected response", result)
    
    @patch('llm_handler.requests.post')
    def test_empty_response(self, mock_post):
        """Edge case: empty LLM response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "   "}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = query_ollama("Test prompt")
        
        self.assertEqual(result, "")
    
    @patch('llm_handler.requests.post')
    def test_long_response(self, mock_post):
        """Edge case: very long response"""
        long_text = "The answer is " * 1000
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": long_text}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = query_ollama("Test prompt")
        
        self.assertIn("The answer is", result)
        self.assertGreater(len(result), 1000)
    
    @patch('llm_handler.requests.post')
    def test_temperature_parameter(self, mock_post):
        """Validation: temperature parameter"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "Answer"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        query_ollama("Test", temperature=0.5)
        
        # Verify the temperature was passed correctly
        call_args = mock_post.call_args
        payload = call_args.kwargs['json']
        self.assertEqual(payload['options']['temperature'], 0.5)


class TestGetAnswer(unittest.TestCase):
    """Test the get_answer orchestration function"""
    
    @patch('llm_handler.query_ollama')
    @patch('llm_handler.format_prompt')
    def test_successful_answer(self, mock_format, mock_query):
        """Happy path: get answer"""
        mock_format.return_value = "Formatted prompt"
        mock_query.return_value = "The answer is correct"
        
        question = "What is true?"
        chunks = ["Context about truth"]
        
        result = get_answer(question, chunks)
        
        self.assertEqual(result["answer"], "The answer is correct")
        self.assertEqual(result["sources"], chunks)
    
    @patch('llm_handler.query_ollama')
    @patch('llm_handler.format_prompt')
    def test_error_gracefully_included(self, mock_format, mock_query):
        """Happy path: error message included in response"""
        mock_format.return_value = "Formatted prompt"
        mock_query.return_value = "Error: Connection failed"
        
        result = get_answer("What?", ["context"])
        
        self.assertIn("Error", result["answer"])
        self.assertEqual(result["sources"], ["context"])
    
    def test_empty_question(self):
        """Error: empty question"""
        with self.assertRaises(ValueError):
            get_answer("", ["context"])
    
    def test_empty_chunks(self):
        """Error: empty chunks"""
        with self.assertRaises(ValueError):
            get_answer("What?", [])
    
    @patch('llm_handler.query_ollama')
    @patch('llm_handler.format_prompt')
    def test_answer_with_multiple_sources(self, mock_format, mock_query):
        """Happy path: answer with multiple source chunks"""
        mock_format.return_value = "Prompt"
        mock_query.return_value = "Answer"
        
        question = "What?"
        chunks = ["chunk1", "chunk2", "chunk3"]
        
        result = get_answer(question, chunks)
        
        self.assertEqual(len(result["sources"]), 3)
        self.assertEqual(result["sources"][0], "chunk1")


class TestCheckOllamaStatus(unittest.TestCase):
    """Test the Ollama health check"""
    
    @patch('llm_handler.requests.get')
    def test_ollama_running(self, mock_get):
        """Happy path: Ollama is running"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = check_ollama_status()
        
        self.assertTrue(result)
    
    @patch('llm_handler.requests.get')
    def test_ollama_not_running(self, mock_get):
        """Error: Ollama not running"""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = check_ollama_status()
        
        self.assertFalse(result)
    
    @patch('llm_handler.requests.get')
    def test_ollama_bad_response(self, mock_get):
        """Error: Ollama bad response"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = check_ollama_status()
        
        self.assertFalse(result)
    
    @patch('llm_handler.requests.get')
    def test_ollama_timeout(self, mock_get):
        """Error: Ollama timeout"""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = check_ollama_status()
        
        self.assertFalse(result)


class TestListAvailableModels(unittest.TestCase):
    """Test the list_available_models function"""
    
    @patch('llm_handler.requests.get')
    def test_list_models_success(self, mock_get):
        """Happy path: list models"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:latest"},
                {"name": "phi3:latest"},
                {"name": "mistral:latest"}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = list_available_models()
        
        self.assertEqual(len(result), 3)
        self.assertIn("llama3:latest", result)
    
    @patch('llm_handler.requests.get')
    def test_list_models_empty(self, mock_get):
        """Edge case: no models installed"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = list_available_models()
        
        self.assertEqual(len(result), 0)
    
    @patch('llm_handler.requests.get')
    def test_list_models_error(self, mock_get):
        """Error: connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = list_available_models()
        
        self.assertEqual(result, [])
    
    @patch('llm_handler.requests.get')
    def test_list_models_timeout(self, mock_get):
        """Error: timeout"""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = list_available_models()
        
        self.assertEqual(result, [])


class TestErrorHandling(unittest.TestCase):
    """Test error message quality"""
    
    @patch('llm_handler.requests.post')
    def test_connection_error_message_helpful(self, mock_post):
        """Validation: connection error message is helpful"""
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        result = query_ollama("Test prompt")
        
        self.assertIn("ollama serve", result)
        self.assertIn("terminal", result)
    
    @patch('llm_handler.requests.post')
    def test_timeout_error_message_helpful(self, mock_post):
        """Validation: timeout error message is helpful"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = query_ollama("Test prompt")
        
        self.assertIn("phi3", result)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    @patch('llm_handler.query_ollama')
    @patch('llm_handler.requests.get')
    def test_full_qa_flow(self, mock_get, mock_query):
        """Integration: health check → format → query → answer"""
        # Health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        status = check_ollama_status()
        self.assertTrue(status)
        
        # Get answer
        mock_query.return_value = "Yes, that's correct"
        
        result = get_answer(
            "Is 2+2=4?",
            ["Math context here"]
        )
        
        self.assertIn("correct", result["answer"])
        self.assertEqual(len(result["sources"]), 1)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

# Coverage command:
# python -m pytest test_llm_handler.py --cov=llm_handler --cov-report=html

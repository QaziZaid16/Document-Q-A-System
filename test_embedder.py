"""
test_embedder.py
================
Test suite for embedder.py

Coverage Goals:
  - embed_chunks: 85%+ 
  - build_faiss_index: 90%+
  - retrieve_relevant_chunks: 90%+
  - save/load index: 95%+
  - build_or_load_index: 85%+

Test Categories:
  1. Happy path: Normal usage
  2. Edge cases: Empty lists, single items, large datasets
  3. Error scenarios: Invalid inputs, corrupted files
  4. Persistence: Save/load cycle
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

try:
    from embedder import (
        embed_chunks,
        build_faiss_index,
        retrieve_relevant_chunks,
        save_index,
        load_index,
        build_or_load_index
    )
    import faiss
except ImportError:
    # Skip tests if dependencies not installed
    pass


class TestEmbedChunks(unittest.TestCase):
    """Test the embed_chunks function"""
    
    @patch('embedder.model')
    def test_normal_embedding(self, mock_model):
        """Happy path: embed normal chunks"""
        mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)
        
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        result = embed_chunks(chunks)
        
        self.assertEqual(result.shape, (3, 384))
        self.assertEqual(result.dtype, np.float32)
    
    @patch('embedder.model')
    def test_single_chunk(self, mock_model):
        """Edge case: single chunk"""
        mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        
        chunks = ["single chunk"]
        result = embed_chunks(chunks)
        
        self.assertEqual(result.shape[0], 1)
        self.assertEqual(result.shape[1], 384)
    
    def test_empty_chunks_list(self):
        """Error: empty chunks list"""
        with self.assertRaises(ValueError):
            embed_chunks([])
    
    def test_non_list_input(self):
        """Error: non-list input"""
        with self.assertRaises(TypeError):
            embed_chunks("not a list")
    
    def test_non_string_chunks(self):
        """Error: chunks that aren't strings"""
        with self.assertRaises(TypeError):
            embed_chunks([123, 456, 789])
    
    def test_mixed_type_chunks(self):
        """Error: mixed types in chunks"""
        with self.assertRaises(TypeError):
            embed_chunks(["valid", 123, "also valid"])
    
    @patch('embedder.model')
    def test_large_chunks_list(self, mock_model):
        """Edge case: large number of chunks"""
        mock_model.encode.return_value = np.random.rand(1000, 384).astype(np.float32)
        
        chunks = [f"chunk {i}" for i in range(1000)]
        result = embed_chunks(chunks)
        
        self.assertEqual(result.shape[0], 1000)


class TestBuildFaissIndex(unittest.TestCase):
    """Test the build_faiss_index function"""
    
    def test_normal_index_build(self):
        """Happy path: build index from embeddings"""
        embeddings = np.random.rand(10, 384).astype(np.float32)
        index = build_faiss_index(embeddings)
        
        self.assertEqual(index.ntotal, 10)
        self.assertEqual(index.d, 384)  # dimension
    
    def test_single_vector(self):
        """Edge case: single vector"""
        embeddings = np.random.rand(1, 384).astype(np.float32)
        index = build_faiss_index(embeddings)
        
        self.assertEqual(index.ntotal, 1)
    
    def test_large_vector_set(self):
        """Edge case: large vector set"""
        embeddings = np.random.rand(10000, 384).astype(np.float32)
        index = build_faiss_index(embeddings)
        
        self.assertEqual(index.ntotal, 10000)
    
    def test_non_numpy_input(self):
        """Error: non-numpy input"""
        with self.assertRaises(TypeError):
            build_faiss_index([[1, 2, 3]])
    
    def test_1d_array(self):
        """Error: 1D array instead of 2D"""
        embeddings = np.random.rand(384).astype(np.float32)
        with self.assertRaises(ValueError):
            build_faiss_index(embeddings)
    
    def test_empty_embeddings(self):
        """Error: empty embeddings"""
        embeddings = np.array([], dtype=np.float32).reshape(0, 384)
        with self.assertRaises(ValueError):
            build_faiss_index(embeddings)
    
    def test_wrong_dimension(self):
        """Error: wrong embedding dimension"""
        embeddings = np.random.rand(10, 256).astype(np.float32)  # Wrong size
        index = build_faiss_index(embeddings)
        # Should still work but with different dimension
        self.assertEqual(index.d, 256)


class TestSaveLoadIndex(unittest.TestCase):
    """Test save and load functions"""
    
    def setUp(self):
        """Create temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_index(self):
        """Happy path: save index"""
        embeddings = np.random.rand(5, 384).astype(np.float32)
        index = build_faiss_index(embeddings)
        chunks = ["chunk 1", "chunk 2", "chunk 3", "chunk 4", "chunk 5"]
        
        save_index(index, chunks, self.test_dir)
        
        # Verify files created
        self.assertTrue(os.path.exists(f"{self.test_dir}/faiss.index"))
        self.assertTrue(os.path.exists(f"{self.test_dir}/chunks.pkl"))
    
    def test_load_index(self):
        """Happy path: load index"""
        embeddings = np.random.rand(5, 384).astype(np.float32)
        index = build_faiss_index(embeddings)
        chunks = ["chunk 1", "chunk 2", "chunk 3", "chunk 4", "chunk 5"]
        
        save_index(index, chunks, self.test_dir)
        loaded_index, loaded_chunks = load_index(self.test_dir)
        
        self.assertEqual(loaded_index.ntotal, 5)
        self.assertEqual(len(loaded_chunks), 5)
        self.assertEqual(loaded_chunks[0], "chunk 1")
    
    def test_save_load_roundtrip(self):
        """Integration: save then load"""
        original_embeddings = np.random.rand(10, 384).astype(np.float32)
        index = build_faiss_index(original_embeddings)
        chunks = [f"chunk {i}" for i in range(10)]
        
        save_index(index, chunks, self.test_dir)
        loaded_index, loaded_chunks = load_index(self.test_dir)
        
        self.assertEqual(loaded_index.ntotal, index.ntotal)
        self.assertEqual(loaded_chunks, chunks)
    
    def test_load_nonexistent_index(self):
        """Error: load from non-existent path"""
        with self.assertRaises(FileNotFoundError):
            load_index("/nonexistent/path")


class TestRetrieveRelevantChunks(unittest.TestCase):
    """Test the retrieve_relevant_chunks function"""
    
    def setUp(self):
        """Create sample index and chunks"""
        # Create 10 random embeddings
        embeddings = np.random.rand(10, 384).astype(np.float32)
        self.index = build_faiss_index(embeddings)
        self.chunks = [f"chunk {i}" for i in range(10)]
    
    @patch('embedder.model')
    def test_retrieve_top_3(self, mock_model):
        """Happy path: retrieve top 3"""
        # Mock query encoding
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        mock_model.encode.return_value = query_embedding
        
        result = retrieve_relevant_chunks(
            "What is this?",
            self.index,
            self.chunks,
            top_k=3
        )
        
        self.assertEqual(len(result), 3)
        for chunk in result:
            self.assertIn("chunk", chunk)
    
    @patch('embedder.model')
    def test_retrieve_single_chunk(self, mock_model):
        """Edge case: retrieve just 1"""
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        mock_model.encode.return_value = query_embedding
        
        result = retrieve_relevant_chunks(
            "What?",
            self.index,
            self.chunks,
            top_k=1
        )
        
        self.assertEqual(len(result), 1)
    
    @patch('embedder.model')
    def test_retrieve_all_chunks(self, mock_model):
        """Edge case: retrieve all chunks"""
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        mock_model.encode.return_value = query_embedding
        
        result = retrieve_relevant_chunks(
            "What?",
            self.index,
            self.chunks,
            top_k=10
        )
        
        self.assertEqual(len(result), 10)
    
    def test_empty_query(self):
        """Error: empty query"""
        with self.assertRaises(ValueError):
            retrieve_relevant_chunks("", self.index, self.chunks)
    
    def test_invalid_top_k_zero(self):
        """Error: top_k <= 0"""
        with self.assertRaises(ValueError):
            retrieve_relevant_chunks(
                "What?",
                self.index,
                self.chunks,
                top_k=0
            )
    
    def test_invalid_top_k_too_large(self):
        """Error: top_k > number of chunks"""
        with self.assertRaises(ValueError):
            retrieve_relevant_chunks(
                "What?",
                self.index,
                self.chunks,
                top_k=100
            )
    
    def test_empty_chunks(self):
        """Error: empty chunks list"""
        with self.assertRaises(ValueError):
            retrieve_relevant_chunks("What?", self.index, [])


class TestBuildOrLoadIndex(unittest.TestCase):
    """Test the build_or_load_index smart helper"""
    
    def setUp(self):
        """Create temporary directory"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('embedder.embed_chunks')
    @patch('embedder.model')
    def test_build_fresh_index(self, mock_model, mock_embed):
        """Happy path: build fresh index"""
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        embeddings = np.random.rand(3, 384).astype(np.float32)
        mock_embed.return_value = embeddings
        
        index, loaded_chunks = build_or_load_index(chunks, self.test_dir)
        
        self.assertEqual(index.ntotal, 3)
        self.assertEqual(loaded_chunks, chunks)
    
    @patch('embedder.embed_chunks')
    def test_load_existing_index(self, mock_embed):
        """Happy path: load existing index"""
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        
        # First call: build index
        embeddings = np.random.rand(3, 384).astype(np.float32)
        index1 = build_faiss_index(embeddings)
        save_index(index1, chunks, self.test_dir)
        
        # Second call: should load (mock_embed shouldn't be called)
        index2, loaded_chunks = build_or_load_index(chunks, self.test_dir)
        
        mock_embed.assert_not_called()
        self.assertEqual(index2.ntotal, 3)
        self.assertEqual(loaded_chunks, chunks)


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        """Create temporary directory"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('embedder.model')
    def test_full_pipeline(self, mock_model):
        """Integration: embed, build, save, retrieve"""
        chunks = [f"This is chunk {i} about topic X" for i in range(5)]
        embeddings = np.random.rand(5, 384).astype(np.float32)
        mock_model.encode.return_value = embeddings
        
        # Embed chunks
        embedded = embed_chunks(chunks)
        self.assertEqual(embedded.shape[0], 5)
        
        # Build index
        index = build_faiss_index(embedded)
        self.assertEqual(index.ntotal, 5)
        
        # Save
        save_index(index, chunks, self.test_dir)
        self.assertTrue(os.path.exists(f"{self.test_dir}/faiss.index"))
        
        # Load
        loaded_index, loaded_chunks = load_index(self.test_dir)
        self.assertEqual(loaded_index.ntotal, 5)
        self.assertEqual(len(loaded_chunks), 5)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

# Coverage command:
# python -m pytest test_embedder.py --cov=embedder --cov-report=html

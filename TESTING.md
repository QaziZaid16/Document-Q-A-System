# 📋 Testing Guide - Document Q&A System

## Overview

This project includes comprehensive test suites for all modules with >80% code coverage targets. Tests cover:
- ✅ Happy path (normal usage)
- ✅ Edge cases (boundaries, special inputs)
- ✅ Error scenarios (invalid inputs, failures)
- ✅ Integration flows (end-to-end)

---

## Test Files

| File | Module | Tests | Target Coverage |
|------|--------|-------|-----------------|
| `test_pdf_processor.py` | PDF extraction & chunking | 35+ | >85% |
| `test_embedder.py` | Vector embeddings & FAISS | 25+ | >85% |
| `test_llm_handler.py` | LLM querying & prompts | 30+ | >85% |
| `test_app.py` | Streamlit UI logic | 15+ | >80% |

---

## Installation

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-cov coverage
```

---

## Running Tests

### Run All Tests
```bash
# Using pytest
pytest

# Using pytest with verbose output
pytest -v

# Using unittest
python -m unittest discover
```

### Run Specific Test File
```bash
pytest test_pdf_processor.py -v
pytest test_embedder.py -v
pytest test_llm_handler.py -v
pytest test_app.py -v
```

### Run Specific Test Class
```bash
pytest test_pdf_processor.py::TestCleanText -v
pytest test_embedder.py::TestBuildFaissIndex -v
```

### Run Specific Test
```bash
pytest test_pdf_processor.py::TestCleanText::test_normal_text -v
```

---

## Code Coverage

### Generate Coverage Report

```bash
# Using pytest-cov
pytest --cov=pdf_processor --cov=embedder --cov=llm_handler --cov-report=html

# Using coverage directly
coverage run -m pytest
coverage report -m
coverage html  # Creates htmlcov/index.html
```

### View Coverage Report
```bash
# Open in browser
open htmlcov/index.html
```

### Coverage Targets
- **pdf_processor.py**: >85% coverage
- **embedder.py**: >85% coverage
- **llm_handler.py**: >85% coverage
- **app.py**: >80% coverage

---

## Test Structure

### test_pdf_processor.py

#### Test Classes:
1. **TestCleanText** (10 tests)
   - Normal text cleaning
   - Edge cases (empty, whitespace-only)
   - Error handling (non-string input)

2. **TestChunkText** (15 tests)
   - Basic chunking logic
   - Overlap validation
   - Invalid parameters
   - Edge cases (single word, exact size)

3. **TestExtractTextFromPdf** (5 tests)
   - File validation
   - Corrupt PDF handling
   - Multipage PDFs (mocked)

4. **TestProcessPdf** (3 tests)
   - Integration testing
   - Parameter validation
   - Pipeline execution

5. **TestIntegrationEndToEnd** (3 tests)
   - Full processing chain
   - Word reconstruction

### test_embedder.py

#### Test Classes:
1. **TestEmbedChunks** (7 tests)
   - Embedding generation
   - Empty/single/large inputs
   - Type validation

2. **TestBuildFaissIndex** (7 tests)
   - Index creation
   - Vector dimensionality
   - Large vector sets

3. **TestSaveLoadIndex** (4 tests)
   - Persistence (save/load)
   - Roundtrip validation
   - File error handling

4. **TestRetrieveRelevantChunks** (8 tests)
   - Similarity search
   - Top-K retrieval
   - Parameter validation

5. **TestBuildOrLoadIndex** (3 tests)
   - Smart caching logic
   - Disk I/O optimization

### test_llm_handler.py

#### Test Classes:
1. **TestFormatPrompt** (9 tests)
   - Prompt formatting
   - Context injection
   - Special characters
   - Input validation

2. **TestQueryOllama** (8 tests)
   - Successful queries
   - Connection errors
   - Timeouts
   - Malformed responses

3. **TestGetAnswer** (5 tests)
   - End-to-end Q&A
   - Error handling
   - Source attribution

4. **TestCheckOllamaStatus** (4 tests)
   - Health checks
   - Connection validation

5. **TestListAvailableModels** (5 tests)
   - Model enumeration
   - Error handling

### test_app.py

#### Test Classes:
1. **TestSessionStateInitialization** (1 test)
   - State setup

2. **TestPdfUploadFlow** (1 test)
   - Upload flow

3. **TestErrorScenarios** (1 test)
   - Error handling

4. **TestChatInteraction** (1 test)
   - Q&A flow

5. **TestChatHistory** (2 tests)
   - History management

---

## Test Execution Examples

### Example 1: Run PDF Tests
```bash
$ pytest test_pdf_processor.py::TestCleanText -v

test_pdf_processor.py::TestCleanText::test_normal_text PASSED
test_pdf_processor.py::TestCleanText::test_empty_string PASSED
test_pdf_processor.py::TestCleanText::test_whitespace_only PASSED
test_pdf_processor.py::TestCleanText::test_single_word PASSED
test_pdf_processor.py::TestCleanText::test_tabs_and_newlines PASSED
test_pdf_processor.py::TestCleanText::test_multiple_spaces PASSED
test_pdf_processor.py::TestCleanText::test_non_string_input PASSED
test_pdf_processor.py::TestCleanText::test_non_string_list_input PASSED
test_pdf_processor.py::TestCleanText::test_leading_trailing_spaces PASSED
test_pdf_processor.py::TestCleanText::test_unicode_characters PASSED

====== 10 passed in 0.42s ======
```

### Example 2: Full Coverage Report
```bash
$ pytest --cov=pdf_processor --cov-report=term-missing

Name                    Stmts   Miss  Cover   Missing
------------------------------------------------------
pdf_processor.py         120      8    93%    45-48,112-115
test_pdf_processor.py    250      0   100%
------------------------------------------------------
TOTAL                    370      8    97%
```

### Example 3: Generate HTML Report
```bash
$ pytest --cov --cov-report=html
$ open htmlcov/index.html
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'pytest'"
**Solution:**
```bash
pip install pytest pytest-cov
```

### Issue: Tests fail with "Import not resolved"
**Solution:**
These are false positives in VS Code. Tests still run correctly. Ignore or:
```bash
# Install all dependencies
pip install -r requirements.txt
```

### Issue: "ConnectionError" in llm_handler tests
**Solution:**
These tests mock the connection, so Ollama doesn't need to run. Tests use `@patch` decorators.

### Issue: Coverage report shows 0% for some files
**Solution:**
```bash
# Make sure to include the module in coverage
pytest --cov=pdf_processor --cov=embedder --cov=llm_handler --cov-report=html
```

---

## Continuous Integration (CI)

### Run Tests Before Commit
```bash
# Create a pre-commit hook
echo "pytest --cov" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest --cov=.
```

---

## Debugging Tests

### Print Debug Info
```bash
pytest test_pdf_processor.py -v -s  # -s shows print statements
```

### Run Single Test with Debugger
```bash
python -m pdb -m pytest test_pdf_processor.py::TestCleanText::test_normal_text
```

### Generate JUnit Report
```bash
pytest --junit-xml=report.xml
```

---

## Test Quality Checklist

- ✅ Tests cover >80% of code
- ✅ Happy path tests exist
- ✅ Edge case tests exist
- ✅ Error scenario tests exist
- ✅ Error messages are validated
- ✅ Mock objects used appropriately
- ✅ No hardcoded paths/dependencies
- ✅ Tests are independent (can run in any order)
- ✅ All imports are correct
- ✅ Documentation is clear

---

## Adding New Tests

### When Adding Features:
1. Write test first (TDD approach)
2. Implement feature
3. Ensure test passes
4. Check coverage

### Template for New Test:
```python
def test_new_feature(self):
    """Test description: what should happen"""
    # Arrange
    input_data = prepare_test_data()
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    self.assertEqual(result, expected_output)
```

---

## Performance Testing

### Run with Timing
```bash
pytest --durations=10  # Shows 10 slowest tests
```

### Profile Specific Test
```bash
python -m cProfile -m pytest test_embedder.py::TestBuildFaissIndex::test_large_vector_set
```

---

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [coverage.py Documentation](https://coverage.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

---

## Questions?

For issues or questions about tests:
1. Check test file docstrings
2. Run with `-v -s` for verbose output
3. Check coverage report for missing areas
4. Review test comments and docstrings

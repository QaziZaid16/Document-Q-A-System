#!/bin/bash
# Simple wrapper to launch Streamlit app
cd "$(dirname "$0")"
python -m streamlit run app.py --logger.level=error

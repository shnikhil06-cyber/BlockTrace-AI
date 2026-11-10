#!/usr/bin/env bash
# BlockTrace-AI: Quick Start Script for Offline Forensic Dashboard

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    echo "Starting BlockTrace-AI in local offline virtualenv..."
    exec .venv/bin/streamlit run web/app.py --server.headless=false --server.port=8501
else
    echo "Starting BlockTrace-AI with system streamlit..."
    exec streamlit run web/app.py --server.headless=false --server.port=8501
fi

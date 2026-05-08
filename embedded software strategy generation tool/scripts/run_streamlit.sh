#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
if [ -f .env ]; then
    set -a
    # shellcheck source=.env
    source .env
    set +a
fi
python -m streamlit run src/copaw_tool/interfaces/streamlit_app/app.py --server.port 8501

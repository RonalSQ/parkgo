#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --prefer-binary -r requirements.txt
printf 'Park Go: http://127.0.0.1:8000/\nBusiness: http://127.0.0.1:8000/business\n'
exec python -m uvicorn app:app --host 127.0.0.1 --port 8000

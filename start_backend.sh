#!/bin/bash
# Start LLM Anonymization Backend API

cd /home/rooter/llm-anonymization
~/miniconda3/envs/py310/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

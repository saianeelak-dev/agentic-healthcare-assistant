# Agentic Healthcare Assistant

This project implements an **agentic healthcare assistant** aligned to the capstone problem statement.

## Features
- Planner-based multi-step query decomposition
- Appointment slot discovery and booking via a local doctor schedule service (pluggable to real APIs)
- Structured/unstructured patient history ingestion from Excel/PDF
- Retrieval-Augmented Generation (RAG) over patient records and uploaded reports
- External medical information search adapters (PubMed/Medline + WHO ready)
- Long-term memory and execution logs
- Streamlit dashboard for patient/doctor views, tool traces, results, and evaluation metrics
- Evaluation module equivalent to the requested QA-style assessment

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py

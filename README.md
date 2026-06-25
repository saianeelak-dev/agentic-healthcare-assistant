# Agentic Healthcare Assistant

An AI-powered healthcare assistant built using Agentic AI, RAG (Retrieval-Augmented Generation), FAISS vector database, LangChain, Groq LLM, and Streamlit.

This project automates common healthcare administration tasks such as:

- Appointment booking
- Patient history retrieval
- Medical report summarization
- Disease information retrieval
- Memory management
- Agent evaluation and tracing

---

# Project Architecture

User Query
    ↓
Planner Agent
    ↓
+--------------------+
| Goal Decomposition |
+--------------------+
    ↓
+---------------------------------------------+
| History Agent                              |
| Appointment Agent                          |
| Medical Search Agent                       |
+---------------------------------------------+
    ↓
RAG Retrieval + Tool Execution
    ↓
Final Agent
    ↓
Streamlit Dashboard

---

# Features

## Planner Agent

- Interprets user intent
- Identifies patient names
- Detects doctor specialties
- Breaks complex requests into tasks

Examples:

```text
Show medical history of Anjali

Book a cardiologist appointment for Anjali

Summarize Anjali's reports

My father has chronic kidney disease.
Book a nephrologist appointment and summarize treatment methods.
```

## Retrieval-Augmented Generation (RAG)

- FAISS vector database
- Semantic search
- PDF report retrieval
- Patient-based filtering

## Patient History Retrieval

Retrieves:

- Diagnoses
- Medications
- Visit history
- Clinical summaries

Sources:

- records.xlsx
- PDF medical reports

## Appointment Scheduling

Supported specialties:

- General Physician
- Nephrologist
- Cardiologist
- Pulmonologist
- Endocrinologist

Includes schedule reset capability for demonstrations.

## Medical Information Search

Retrieves disease information and treatment summaries using external medical sources.

## Memory

Stores:

- Session memory
- Patient context
- Tool execution traces

## Evaluation

Tracks:

- Relevance Score
- Completeness Score
- Safety Score
- Tool Success Rate

---

# Technology Stack

## Backend

- Python 3.11
- LangChain
- Groq LLM

## Retrieval

- FAISS
- Sentence Transformers
- all-MiniLM-L6-v2

## Data Processing

- Pandas
- OpenPyXL
- PyPDF

## Frontend

- Streamlit

---

# Project Structure

```text
agentic-healthcare-assistant/
│
├── agents/
├── core/
├── data/
├── evaluation/
├── rag/
├── tools/
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
└── .env.example
```

---

# Installation

Clone repository:

```bash
git clone https://github.com/saianeelak-dev/agentic-healthcare-assistant.git

cd agentic-healthcare-assistant
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate:

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key

GROQ_MODEL=llama3-8b-8192

EMBEDDING_MODEL=all-MiniLM-L6-v2

CHUNK_SIZE=800
CHUNK_OVERLAP=120
RETRIEVAL_TOP_K=5
```

---

# Running the Application

```bash
python -m streamlit run app.py
```

---

# Sample Queries

## History Retrieval

```text
Show medical history of Anjali
```

## Report Summarization

```text
Summarize Anjali's reports
```

## Appointment Booking

```text
Book a cardiologist appointment for Anjali
```

## Medical Information Search

```text
What medications is Ramesh taking?
```

## Multi-Agent Workflow

```text
My father has chronic kidney disease.
Book a nephrologist appointment for him.
Also summarize latest treatment methods.
```

---

# Evaluation Dashboard

The dashboard displays:

- Planner output
- Tool traces
- Retrieved documents
- Appointment status
- Evaluation metrics
- Memory information

---

# Future Enhancements

- Real EHR integration
- Real doctor scheduling APIs
- PubMed live retrieval
- Multi-patient memory
- Multi-agent orchestration using LangGraph

---

# Author

Sai Aneela K

GitHub:
https://github.com/saianeelak-dev
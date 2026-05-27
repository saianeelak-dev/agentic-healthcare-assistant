# 🏥 Agentic Healthcare Assistant

An **AI-powered healthcare assistant** built using **RAG, LLMs, and Streamlit** that can:
- Summarize patient history
- Book appointments
- Provide treatment guidance
- Handle multi-step user queries using agentic planning

---

## 🚀 Live Demo

https://agentic-healthcare-assistant-stahtxis4shjwmmidcuyna.streamlit.app/

---

## ⚙️ Features

✅ Agentic AI (Planner + Tools)  
✅ Medical Record Retrieval (Excel + PDF)  
✅ Appointment Booking Simulation  
✅ LLM-based Treatment Guidance  
✅ Memory Logging for transparency  
✅ Evaluation Metrics (Relevance, Completeness, Safety)  

---

## 🧠 Architecture

User Query → Planner → Tools → LLM Final → Evaluation

- Planner breaks query into steps  
- Tools:
  - Patient History Tool
  - Appointment Tool
  - Medical Guidance Tool
- RAG retrieves patient + PDF data  
- LLM synthesizes response  

---

## 📂 Project Structure

├── app.py
├── data/
│   ├── records.xlsx
│   ├── patient reports (pdf)
├── requirements.txt
---

## 🔐 API Key Setup

❌ Do NOT store API keys in repo  

For deployment:

Go to Streamlit Cloud → Secrets → add:

GROQ_API_KEY="your_key"
GROQ_MODEL="llama-3.1-8b-instant"

---

## 🧪 Sample Queries

- "Book appointment for David Thompson and summarize history"
- "Provide treatment for diabetes"
- "My father has CKD – suggest treatment options"

---

## 📊 Evaluation Metrics

- Relevance Score
- Completeness Score
- Safety Score
- LLM-generated feedback

---

## ⚠️ Disclaimer

This system is for educational purposes only and does not replace professional medical advice.

---

## 🏁 Tech Stack

- Python
- Streamlit
- LangChain / Groq API
- Pandas
- RAG (Excel + PDF)

---

## 👨‍💻 Author

Sai Aneela K

https://agentic-healthcare-assistant-stahtxis4shjwmmidcuyna.streamlit.app/

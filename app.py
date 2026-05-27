import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime

PLANNER_SYSTEM = """
You are a planner for an Agentic Healthcare Assistant.
Return ONLY valid minified JSON, no markdown, no explanation.

Schema:
{"steps":["appointment","history","medical"],"patient_name":"","doctor_specialty":""}

Rules:
- Include "appointment" if user wants to book/schedule/see a doctor.
- Include "history" if user asks for history/summary/records/diagnosis/medications.
- Include "medical" if user asks for disease/treatment/latest methods/info.
- steps must be a subset of ["appointment","history","medical"].
- If patient not found in dataset:
    - Do NOT assume identity
    - Provide general guidance only

Return ONLY JSON.
"""

import json
import re
from typing import Any

def safe_json_loads(content: Any) -> dict:
    """
    Robust JSON parser for LLM outputs.
    Handles: empty output, non-JSON text, JSON embedded inside text, list/dict content.
    Returns {} on failure.
    """
    if content is None:
        return {}

    # LangChain sometimes returns list/dict blocks
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        # Convert list blocks to a string then parse if possible
        try:
            content = json.dumps(content, ensure_ascii=False)
        except Exception:
            content = str(content)

    # Now content should be str-like
    text = content if isinstance(content, str) else str(content)
    text = text.strip()
    if not text:
        return {}

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract the first JSON object from the text
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

    return {}


# def safe_json_loads(content: Any) -> dict:
#     if isinstance(content, dict):
#         return content
#     if isinstance(content, str):
#         return json.loads(content)
#     # sometimes content can be list of blocks -> convert to string
#     if isinstance(content, list):
#         return json.loads(json.dumps(content))
#     return json.loads(str(content))

import json
from typing import Any

def to_text(content: Any) -> str:
    """Normalize LLM message content into plain text for safety + type checking."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    # LangChain can return structured blocks (list/dict). Convert to JSON string.
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)

# Optional LLM (Groq)
try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except:
    GROQ_AVAILABLE = False

# Embeddings + FAISS
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# =========================
# CONFIG
# =========================
#GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
#GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
import streamlit as st
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GROQ_MODEL = st.secrets.get("GROQ_MODEL", "llama3-8b-8192")


FINAL_SYSTEM = """
You are an Agentic Healthcare Assistant (educational demo).
Create a concise Markdown response with headings:
1) Patient Summary
2) Appointment Status
3) Treatment Guidance (grounded in retrieved context)
4) Follow-up Actions
5) Disclaimer (not medical advice)

If no patient is found in the records:
- Do NOT assume any patient name
- Provide general medical guidance only

If Known Patient is False:
- Do NOT assign any patient name
- Do NOT infer identity
- Provide general medical guidance only

If HISTORY contains "No matching patient":
- Do NOT mention any patient name
- Provide general medical guidance

"""

EVAL_SYSTEM = """
You are evaluating an AI assistant response.
Give a JSON with:
- relevance_score (1-5)
- completeness_score (1-5)
- safety_score (1-5)
- brief_comment
Return only JSON.
"""

# =========================
# MEMORY MODULE
# =========================
class MemoryManager:
    def __init__(self):
        self.logs = []

    def add(self, step, data):
        self.logs.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "step": step,
            "data": str(data)
        })

    def get_logs(self):
        return self.logs

# =========================
# PATIENT DATA MANAGEMENT
# =========================
from pypdf import PdfReader
import os
import pandas as pd
import re

class PatientManager:
    def __init__(self):
        self.df = pd.DataFrame()

    def load_data(self):
        base_dir = os.path.join(os.getcwd(), "data")

        # Excel: prefer data/records.xlsx, fallback to root records.xlsx
        excel_path = os.path.join(base_dir, "records.xlsx")
        if not os.path.exists(excel_path):
            excel_path = "records.xlsx"

        try:
            df = pd.read_excel(excel_path)
        except Exception:
            df = pd.DataFrame()

        # PDFs to load (prefer from data/)
        pdf_files = [
            "sample_patient.pdf",
            "sample_report_anjali.pdf",
            "sample_report_david.pdf",
            "sample_report_ramesh.pdf",
        ]

        rows = []
        for f in pdf_files:
            pdf_path = os.path.join(base_dir, f)
            if not os.path.exists(pdf_path):
                pdf_path = f

            if os.path.exists(pdf_path):
                try:
                    reader = PdfReader(pdf_path)
                    text = ""
                    for page in reader.pages:
                        text += (page.extract_text() or "") + "\n"
                    rows.append({"text": text.strip(), "source": f})
                except Exception as e:
                    rows.append({"text": f"Error reading {f}: {e}", "source": f})

        pdf_df = pd.DataFrame(rows)

        # Combine Excel + PDF text into one dataframe
        self.df = pd.concat([df, pdf_df], ignore_index=True)

    def _find_patient_name(self, query: str):
        if self.df.empty or "Name" not in self.df.columns:
            return None

        names = self.df["Name"].dropna().astype(str).unique().tolist()
        q = query.lower()

        for name in names:
        #STRICT FULL NAME MATCH ONLY
            if name.lower() in q:
                return name

        return None

  
    def _format_patient_card(self, row: dict, pdf_text: str | None = None) -> str:
        lines = []
        lines.append(f"### Patient: {row.get('Name','')}")
        lines.append(f"- **Age/Gender:** {row.get('Age','')} / {row.get('Gender','')}")
        lines.append(f"- **Phone:** {row.get('Phone_number','')}")
        email = row.get("Email")
        if pd.notna(email):
            lines.append(f"Email: {email}")
        if row.get("Email"):
            lines.append(f"- **Email:** {row.get('Email')}")
        lines.append(f"- **Address:** {row.get('Address','')}")
        if row.get("Summary"):
            lines.append(f"- **Summary:** {row.get('Summary')}")
        if pdf_text:
            # keep it short so UI stays clean
            snippet = pdf_text.strip()
            snippet = re.sub(r"\s+", " ", snippet)
            lines.append(f"- **PDF Notes (snippet):** {snippet[:600]}{'...' if len(snippet) > 600 else ''}")
        return "\n".join(lines)

    def search(self, query: str):
        if self.df.empty:
            return "No patient data available"

        # split structured excel rows vs pdf rows
        if "Name" in self.df.columns:
            excel_df = self.df[self.df["Name"].notna()]
        else:
            excel_df = pd.DataFrame()
        if "text" in self.df.columns:
            pdf_df = self.df[self.df["text"].notna()]
        else:
            pdf_df = pd.DataFrame()
        
        # If user asks for all patients
        if "all patients" in query.lower() or "all patient" in query.lower():
            if excel_df.empty:
                return "No structured patient records found."
            cards = []
            for _, r in excel_df.iterrows():
                row = r.to_dict()
                # try to find matching pdf text by name
                pdf_text = None
                if not pdf_df.empty:
                    hits = pdf_df[pdf_df["text"].astype(str).str.contains(str(row.get("Name","")), case=False, na=False)]
                    if not hits.empty:
                        pdf_text = hits.iloc[0].get("text")
                cards.append(self._format_patient_card(row, pdf_text))
            return "\n\n---\n\n".join(cards)

        # Otherwise: try match a specific patient
        name = self._find_patient_name(query)
        if name:
            # normal behavior (existing patient)
            hit = self.df[self.df["Name"].astype(str).str.lower() == name.lower()]
            if not hit.empty:
                row = hit.iloc[0].to_dict()
                return self._format_patient_card(row)
        print("Detected name:", name)
        # NEW: HANDLE UNKNOWN PATIENT
        #return "No matching patient found in records. Providing general medical guidance only."
        return {
            "status": "unknown",
            "message": "No matching patient found in records."
        }
        if not excel_df.empty:
            cards = []
            for _, r in excel_df.head(3).iterrows():
                cards.append(self._format_patient_card(r.to_dict()))
            return "\n\n---\n\n".join(cards)
        return "No structured patient records found."
        # if name and not excel_df.empty:
        #     hit = excel_df[excel_df["Name"].astype(str).str.lower() == name.lower()]
        #     if not hit.empty:
        #         row = hit.iloc[0].to_dict()
        #         pdf_text = None
        #         if not pdf_df.empty:
        #             hits = pdf_df[pdf_df["text"].astype(str).str.contains(name, case=False, na=False)]
        #             if not hits.empty:
        #                 pdf_text = hits.iloc[0].get("text")
        #         return self._format_patient_card(row, pdf_text)

        # fallback: show top structured records only (clean)
        
    # def search(self, query: str):
    #     if self.df.empty:
    #         return "No patient data available"

    #     # If Excel has Name column, try filtering by a name token
    #     if "Name" in self.df.columns:
    #         for name in self.df["Name"].dropna().astype(str).unique():
    #             if name.lower() in query.lower():
    #                 return self.df[self.df["Name"].astype(str).str.lower() == name.lower()].to_string(index=False)

    #     # Otherwise show a sample of loaded content
    #     return self.df.head(5).to_string(index=False)


# =========================
# VECTOR STORE (RAG)
# =========================
class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.texts = []

    def build(self, texts):
        self.texts = texts
        embeddings = self.model.encode(texts)
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings))

    def search(self, query, k=2):
        if not self.index:
            return []

        q_emb = self.model.encode([query])
        D, I = self.index.search(np.array(q_emb), k)

        return [self.texts[i] for i in I[0]]
    
    def build_from_texts(self, texts: list[str]):
        embeds = self.model.encode(texts, convert_to_numpy=True).astype("float32")
        self.index = faiss.IndexFlatL2(embeds.shape[1])
        self.index.add(embeds)
        self.texts = texts

    def retrieve(self, query: str, k: int = 3):
        if self.index is None:
           return []
        q_emb = self.model.encode([query], convert_to_numpy=True).astype("float32")
        _, idx = self.index.search(q_emb, k)
        return [self.texts[i] for i in idx[0] if i < len(self.texts)]

# =========================
# TOOLS
# =========================
class AppointmentTool:
    def book(self, patient, doctor):
        return f"Placeholder appointment booked (demo system – no real scheduling API) for {patient} with {doctor} on next available slot."

class MedicalSearchTool:
    def search(self, query):
        return f"Latest info about {query}: Lifestyle changes, medication, and monitoring."

# =========================
# AGENT
# =========================
class HealthcareAgent:
    def __init__(self):
        self.memory = MemoryManager()
        self.patient_manager = PatientManager()
        self.vector = VectorStore()
        self.appointment_tool = AppointmentTool()
        self.medical_tool = MedicalSearchTool()

        self.patient_manager.load_data()
        # Build RAG knowledge base from patient summaries + pdf text
        kb_texts = []
        if "Summary" in self.patient_manager.df.columns:
            kb_texts += self.patient_manager.df["Summary"].dropna().astype(str).tolist()
        if "text" in self.patient_manager.df.columns:
            kb_texts += self.patient_manager.df["text"].dropna().astype(str).tolist()

        if kb_texts:
            self.vector.build_from_texts(kb_texts)
            self.memory.add("RAG", f"Built vector store with {len(kb_texts)} documents")
        #self.vector.build(["kidney disease treatment", "diabetes management", "hypertension care"])

        if GROQ_AVAILABLE and GROQ_API_KEY:
            self.llm = ChatGroq(model=GROQ_MODEL, temperature = 0)
        else:
            self.llm = None

    def plan(self, query: str):
        # LLM-first planning (capstone aligned)
        if not self.llm:
            # fallback (but for capstone, you should set the key)
            steps = []
            q = query.lower()
            if "book" in q: steps.append("appointment")
            if "summary" in q or "history" in q: steps.append("history")
            if "treatment" in q or "disease" in q: steps.append("medical")
            self.memory.add("Plan", steps)
            return steps, "", ""

        msg = self.llm.invoke([
            ("system", PLANNER_SYSTEM),
            ("human", query)
        ])

        plan_json = safe_json_loads(msg.content)
        if not plan_json or "steps" not in plan_json:
            # fallback rule-based plan (keeps your app running)
            steps = []
            q = query.lower()
            if "book" in q or "appointment" in q or "schedule" in q:
                steps.append("appointment")
            if "summary" in q or "history" in q or "record" in q:
                steps.append("history")
            if "treatment" in q or "disease" in q or "latest" in q:
                steps.append("medical")

            plan_json = {"steps": steps, "patient_name": "", "doctor_specialty": ""}
        steps = plan_json.get("steps", [])
        patient_name = plan_json.get("patient_name", "")
        specialty = plan_json.get("doctor_specialty", "")
        self.memory.add("Plan", plan_json)
        return steps, patient_name, specialty

    def finalize(self, query: str, appointment_out: str, history_out: str, medical_out: str, is_known_patient) -> str:
        if not self.llm:
            return (
                "## Patient Summary\n" + (history_out or "Not available") + "\n\n"
                "## Appointment Status\n" + (appointment_out or "Not requested") + "\n\n"
                "## Treatment Guidance\n" + (medical_out or "Not requested") + "\n\n"
                "## Follow-up Actions\n- Follow clinician guidance\n- Complete recommended labs\n\n"
                "## Disclaimer\nEducational only. Not medical advice.\n"
            )

        prompt = f"""USER QUERY:
    {query}

    Known Patient: {is_known_patient}

    APPOINTMENT:
    {appointment_out}

    HISTORY:
    {history_out}

    MEDICAL (RAG/tool output):
    {medical_out}

    RULE:
    If Known Patient is False:
    - Do NOT assign any patient name
    - Provide only general guidance

    """

        msg = self.llm.invoke([("system", FINAL_SYSTEM), ("human", prompt)])
        content = msg.content
        if not isinstance(content, str):
            content = json.dumps(content)
        return content
  
    def evaluate(self, query: str, final_answer: str):
        if not self.llm:
            return {"relevance_score": None, "completeness_score": None, "safety_score": None, "brief_comment": "LLM disabled"}
        msg = self.llm.invoke([
        ("system", EVAL_SYSTEM),
        ("human", f"QUERY:\n{query}\n\nANSWER:\n{final_answer}")
        ])
        
        #import json
        #content = msg.content
        #if not isinstance(content, str):
        #    content = json.dumps(content)
        #return json.loads(msg.content)
        content_str = to_text(msg.content)
        return json.loads(content_str)
  
    def run(self, query: str):   
        results = {}
        appointment_out = ""
        history_out = ""
        medical_out = ""
        rag_context = ""
        is_known_patient = False

        steps, patient_name, specialty = self.plan(query)

        for step in steps:
            if step == "appointment":
                appointment_out = self.appointment_tool.book(patient_name or "Patient", specialty or "Doctor")
                #results["appointment"] = appointment_out
                self.memory.add("Appointment", appointment_out)

            elif step == "history":
                history_result = self.patient_manager.search(query)
                if isinstance(history_result, dict) and history_result.get("status") == "unknown":
                    history_out = history_result["message"]
                    is_known_patient = False
                else:
                    history_out = str(history_result)
                    is_known_patient = True
                results["history"] = history_out

                self.memory.add("History", history_out)

            elif step == "medical":
                # 1) Retrieve relevant chunks from FAISS
                rag_chunks = self.vector.retrieve(query, k=3)   
                # or self.vector.search(...) depending on your method name
                rag_context = "\n\n".join(rag_chunks) if rag_chunks else "No relevant context retrieved."

                # 2) Use LLM to summarize grounded on retrieved context
                if self.llm:
                    med_msg = self.llm.invoke([
                        ("system", "Summarize treatment guidance based only on provided context. If missing, say so."),
                        ("human", f"Query: {query}\n\nContext:\n{rag_context}")
                    ])
                    medical_out = to_text(med_msg.content) if hasattr(med_msg, "content") else str(med_msg)
                else:
                    # fallback if LLM disabled
                    medical_out = self.medical_tool.search(query) + "\n\nRAG Context:\n" + rag_context

                results["medical"] = medical_out
                self.memory.add("Medical", medical_out)
               
        results["final"] = self.finalize(query, appointment_out, history_out, medical_out, is_known_patient)
        results["evaluation"] = self.evaluate(query, results["final"])
        self.memory.add("Evaluation", results["evaluation"])
        #self.memory.add("Final", results["final"])
        return results
      

# =========================
# STREAMLIT UI
# =========================

def render_main_ui():
    st.title("🏥 Agentic Healthcare Assistant")  
    
#    import os
#    st.subheader("DEBUG: Paths")
#    st.write("CWD:", os.getcwd())
#    st.write("Root files:", os.listdir(os.getcwd()))
#    st.write("data/ exists:", os.path.exists("data"))
#  if os.path.exists("data"):
#        st.write("data files:", os.listdir("data"))
#       st.write("records.xlsx exists:", os.path.exists("records.xlsx"))
#       st.write("data/records.xlsx exists:", os.path.exists("data/records.xlsx"))

    agent = HealthcareAgent()

    query = st.text_input("Enter your request")

    if st.button("Run") and query:
        results = agent.run(query)

        # MAIN FINAL ANSWER
        st.markdown(results["final"])

        # SHOW EVALUATION (LLMOps)
        if "evaluation" in results:
            with st.expander("Evaluation Metrics (LLMOps)", expanded=False):
                st.json(results["evaluation"])

        # OPTIONAL MEMORY LOGS
        with st.expander("Memory Logs", expanded=False):
            logs = pd.DataFrame(agent.memory.get_logs())
            st.dataframe(logs, use_container_width=True)

            # st.subheader("Results")
            # for k, v in results.items():
            #     st.write(f"**{k.upper()}**")
            #     st.write(v)

            # st.subheader("Memory Logs")
            # logs = pd.DataFrame(agent.memory.get_logs())
            # st.dataframe(logs, width="stretch")

# =========================
# CLI MODE
# =========================
def run_cli():
    agent = HealthcareAgent()
    while True:
        query = input("Enter request: ").strip()
        if query.lower() == "exit":
            break
        print(agent.run(query))

# =========================
# ENTRY POINT FIXED
# =========================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli()
    else:
        render_main_ui()

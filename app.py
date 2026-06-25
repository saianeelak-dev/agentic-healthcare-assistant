from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import pandas as pd
import streamlit as st
from main import HealthcareAssistant
from core.config import settings
from data.loaders import load_all_data

st.write("App startup: app.py loaded successfully")
print("DEBUG: app.py started")

st.set_page_config(page_title='Agentic Healthcare Assistant', page_icon='🏥', layout='wide')
st.title('🏥 Agentic Healthcare Assistant')
st.caption('Planner + tools + memory + RAG + evaluation dashboard')

@st.cache_resource(show_spinner=False)
def get_assistant() -> HealthcareAssistant:
    return HealthcareAssistant()


assistant = None
startup_error = None

try:
    assistant = get_assistant()
except Exception as e:
    startup_error = str(e)

if startup_error:
    st.error(f"Startup failed: {startup_error}")
    st.stop()

assistant = get_assistant()
loaded = load_all_data(settings.data_dir)
records_df = loaded['records']
pdf_texts = loaded['pdf_texts']

with st.sidebar:
    st.header('System Design')
    st.write('Embedding model:', settings.embedding_model)
    st.write('Vector DB:', 'FAISS IndexFlatIP (cosine via normalized embeddings)')
    st.write('Chunk size:', settings.chunk_size)
    st.write('Chunk overlap:', settings.chunk_overlap)
    st.write('Top-k retrieval:', settings.retrieval_top_k)
    st.write('Data dir:', settings.data_dir)
    
    st.subheader("Doctor Schedule Controls")

    if st.button("Reset appointment slots"):
        trace = assistant.doctor_tool.reset_slots()
        st.success(trace.output_summary)

query = st.text_area(
    'Enter a patient/admin request',
    value='My 70-year-old uncle has chronic kidney disease. I want to book a nephrologist for him. Also, can you summarize latest treatment methods?',
    height=120
)
run = st.button('Run assistant', type='primary')

if run and query.strip():
    result = assistant.run(query.strip())
    tab1, tab2, tab3, tab4 = st.tabs(['Assistant Response', 'Planning & Tool Traces', 'Patients / Doctors', 'Evaluation & Memory'])

    with tab1:
        st.markdown(result.final_markdown)
        with st.expander('Retrieved context'):
            for hit in result.retrieved_context:
                st.markdown(f"**{hit.source_file}** | score={hit.score:.3f} | patient={hit.patient_name}")
                st.write(hit.text)

    with tab2:
        st.subheader('Plan')
        st.json(asdict(result.plan))
        st.subheader('Tool traces')
        st.json([asdict(t) for t in result.tool_traces])

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Patient view')
            if isinstance(records_df, pd.DataFrame) and not records_df.empty:
                st.dataframe(records_df, use_container_width=True)
            else:
                st.info('No records.xlsx loaded from data/.')
            st.subheader('Loaded PDFs')
            st.write(list(pdf_texts.keys()) or 'No PDFs loaded')
        with col2:
            st.subheader('Doctor schedule')
            schedule_path = Path(settings.data_dir) / 'doctor_schedule.csv'
            if schedule_path.exists():
                st.dataframe(pd.read_csv(schedule_path), use_container_width=True)
            else:
                st.info('No doctor schedule found.')

    with tab4:
        st.subheader('Evaluation metrics')
        st.json(result.evaluation)
        st.subheader('Session memory log')
        mem_file = Path(settings.memory_dir) / 'session_memory.jsonl'
        if mem_file.exists():
            st.code(mem_file.read_text(encoding='utf-8')[-5000:])
        else:
            st.info('No memory traces yet.')
else:
    st.info('Load your data files into data/ and run a query to see planning, tool traces, booking, RAG retrieval, and evaluation telemetry.')
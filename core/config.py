from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    vector_index_path: str = os.getenv("VECTOR_INDEX_PATH", "storage/faiss.index")
    vector_meta_path: str = os.getenv("VECTOR_META_PATH", "storage/vector_meta.json")
    memory_dir: str = os.getenv("MEMORY_DIR", "storage")
    logs_dir: str = os.getenv("LOGS_DIR", "logs")
    data_dir: str = os.getenv("DATA_DIR", "data")
    ncbi_tool: str = os.getenv("NCBI_TOOL", "agentic-healthcare-assistant")
    ncbi_email: str = os.getenv("NCBI_EMAIL", "")
    user_agent: str = os.getenv("USER_AGENT", "agentic-healthcare-assistant/1.0")

settings = Settings()
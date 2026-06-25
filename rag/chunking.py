
from __future__ import annotations

from typing import List, Dict, Any, Optional
import re
import pandas as pd

from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings
from core.models import ChunkRecord


def _guess_patient_name(text: str) -> Optional[str]:
    patterns = [
        r"Patient:\s*([A-Za-z]+\s+[A-Za-z]+)",
        r"^([A-Z][a-z]+\s+[A-Z][a-z]+)"
    ]

    for pat in patterns:
        match = re.search(pat, text, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()

    return None


def build_documents(
    records_df: pd.DataFrame,
    pdf_texts: Dict[str, str],
) -> List[Dict[str, Any]]:

    docs: List[Dict[str,Any]] = []

    if not records_df.empty:

        for _, row in records_df.fillna("").iterrows():

            patient_name = str(row.get("Name", "")).strip() or None

            text = "\n".join(
                [
                    f"Name: {row.get('Name', '')}",
                    f"Phone: {row.get('Phone_number', '')}",
                    f"Email: {row.get('Email', '')}",
                    f"Age: {row.get('Age', '')}",
                    f"Gender: {row.get('Gender', '')}",
                    f"Address: {row.get('Address', '')}",
                    f"Summary: {row.get('Summary', '')}",
                ]
            )

            docs.append(
                {
                    "source_file": "records.xlsx",
                    "patient_name": patient_name,
                    "doc_type": "structured_record",
                    "text": text,
                }
            )

    for source_file, text in pdf_texts.items():

        docs.append(
            {
                "source_file": source_file,
                "patient_name": _guess_patient_name(text),
                "doc_type": "pdf_record",
                "text": text,
            }
        )

    return docs


def chunk_documents(
    docs: List[Dict[str, Any]]
) -> List[ChunkRecord]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks:List[ChunkRecord] = []
    counter = 0

    for doc in docs:

        pieces = splitter.split_text(doc["text"])

        for chunk_text in pieces:

            counter += 1

            chunks.append(
                ChunkRecord(
                    chunk_id=f"ch_{counter:05d}",
                    source_file=doc["source_file"],
                    patient_name=doc.get("patient_name"),
                    text=chunk_text,
                    metadata={
                        "doc_type": doc.get("doc_type")
                    },
                )
            )

    return chunks

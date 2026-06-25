
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, cast

import pandas as pd

from core.models import ToolTrace


class EHRTool:
    def __init__(self, records_df: pd.DataFrame) -> None:
        self.records_df = records_df.fillna("") if records_df is not None else pd.DataFrame()

    def find_patient(self, patient_name: str) -> Tuple[Optional[Dict[str, Any]], ToolTrace]:
        if self.records_df.empty or not patient_name:
            trace = ToolTrace(
                "ehr_find_patient",
                {"patient_name": patient_name},
                False,
                "No patient records loaded",
            )
            return None, trace

        mask = (
            self.records_df["Name"]
            .astype(str)
            .str.lower()
            .str.contains(patient_name.lower(),na=False))
        rows = self.records_df[mask]

        if rows.empty:
            trace = ToolTrace(
                "ehr_find_patient",
                {"patient_name": patient_name},
                False,
                "Patient not found in records.xlsx",
            )
            return None, trace

        record = cast(Dict[str, Any], rows.iloc[0].to_dict())

        trace = ToolTrace(
            "ehr_find_patient",
            {"patient_name": patient_name},
            True,
            f"Found patient {record.get('Name', '')}",
        )
        return record, trace

    def update_or_add_patient(self, payload: Dict[str, Any]) -> ToolTrace:
        if self.records_df.empty:
            self.records_df = pd.DataFrame([payload])
        else:
            name = str(payload.get("Name", "")).strip().lower()
            mask = self.records_df["Name"].astype(str).str.strip().str.lower() == name

            if mask.any():
                idx = self.records_df[mask].index[0]
                for k, v in payload.items():
                    self.records_df.at[idx, k] = v
                summary = f"Updated patient {payload.get('Name', '')}"
            else:
                self.records_df = pd.concat([self.records_df, pd.DataFrame([payload])], ignore_index=True)
                summary = f"Added patient {payload.get('Name', '')}"

        return ToolTrace("ehr_update_or_add", payload, True, summary)

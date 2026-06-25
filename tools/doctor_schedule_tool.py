from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import pandas as pd

from core.models import AppointmentResult, ToolTrace


class DoctorScheduleTool:
    def __init__(self, data_dir: str = "data", consume_bookings: bool = False) -> None:
        """
        consume_bookings = False  -> demo mode (repeatable bookings, slots stay available)
        consume_bookings = True   -> realistic mode (slot becomes unavailable after booking)
        """
        self.path = Path(data_dir) / "doctor_schedule.csv"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.consume_bookings = consume_bookings

        if not self.path.exists():
            self._seed_default_schedule()

        self.df = pd.read_csv(self.path)

        # Safety: ensure required columns exist
        expected_cols = {"doctor_name", "specialty", "slot", "available"}
        if not expected_cols.issubset(set(self.df.columns)):
            self._seed_default_schedule()
            self.df = pd.read_csv(self.path)

    def _default_schedule_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "doctor_name": "Dr. Neha Iyer",
                "specialty": "general physician",
                "slot": "2026-06-25 10:00",
                "available": True,
            },
            {
                "doctor_name": "Dr. Arjun Rao",
                "specialty": "nephrologist",
                "slot": "2026-06-25 11:30",
                "available": True,
            },
            {
                "doctor_name": "Dr. Asha Menon",
                "specialty": "pulmonologist",
                "slot": "2026-06-25 16:00",
                "available": True,
            },
            {
                "doctor_name": "Dr. Vikram Shah",
                "specialty": "cardiologist",
                "slot": "2026-06-26 09:30",
                "available": True,
            },
            {
                "doctor_name": "Dr. Meera Nair",
                "specialty": "endocrinologist",
                "slot": "2026-06-26 14:00",
                "available": True,
            },
        ]

    def _seed_default_schedule(self) -> None:
        seed = pd.DataFrame(self._default_schedule_rows())
        seed.to_csv(self.path, index=False)

    def reload(self) -> None:
        """Reload latest CSV content from disk."""
        self.df = pd.read_csv(self.path)

    def reset_slots(self) -> ToolTrace:
        """
        Reset all slots back to available=True.
        Useful for Streamlit demo / repeated testing.
        """
        self._seed_default_schedule()
        self.reload()
        return ToolTrace(
            "doctor_schedule_reset",
            {"path": str(self.path)},
            True,
            "Doctor schedule reset successfully. All default slots are now available.",
        )

    def view_schedule(self) -> pd.DataFrame:
        """Return the current schedule dataframe."""
        self.reload()
        return self.df.copy()

    def find_next_available(self, specialty: str) -> Tuple[Optional[dict], ToolTrace]:
        self.reload()

        if not specialty or not str(specialty).strip():
            return (
                None,
                ToolTrace(
                    "doctor_schedule_find",
                    {"specialty": specialty},
                    False,
                    "No specialty provided",
                ),
            )

        specialty = specialty.strip().lower()

        # robust matching: exact normalized string match
        rows = self.df[
            (self.df["specialty"].astype(str).str.strip().str.lower() == specialty)
            & (self.df["available"] == True)
        ]

        if rows.empty:
            return (
                None,
                ToolTrace(
                    "doctor_schedule_find",
                    {"specialty": specialty},
                    False,
                    f"No available slots for {specialty}",
                ),
            )

        row = rows.iloc[0].to_dict()

        print("SPECIALTY:", specialty)
        print("MATCHED ROWS:")
        print(rows)

        return (
            row,
            ToolTrace(
                "doctor_schedule_find",
                {"specialty": specialty},
                True,
                f"Found slot {row['slot']} with {row['doctor_name']}",
            ),
        )

    def book(self, patient_name: str, specialty: str):
        slot_row, trace1 = self.find_next_available(specialty)
        traces = [trace1]

        if not slot_row:
            return (
                AppointmentResult(
                    success=False,
                    specialty=specialty,
                    message=trace1.output_summary,
                ),
                traces,
            )

        # Only consume the slot if realistic mode is enabled
        if self.consume_bookings:
            mask = (
                (self.df["doctor_name"] == slot_row["doctor_name"])
                & (self.df["slot"] == slot_row["slot"])
            )
            self.df.loc[mask, "available"] = False
            self.df.to_csv(self.path, index=False)

        result = AppointmentResult(
            success=True,
            doctor_name=slot_row["doctor_name"],
            specialty=specialty,
            slot=slot_row["slot"],
            message=(
                f"Booked {patient_name or 'patient'} with "
                f"{slot_row['doctor_name']} ({specialty}) at {slot_row['slot']}"
            ),
        )

        traces.append(
            ToolTrace(
                "doctor_schedule_book",
                {"patient_name": patient_name, "specialty": specialty},
                True,
                result.message,
            )
        )

        return result, traces

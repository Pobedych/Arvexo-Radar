"""Controlled filesystem storage for uploaded datasets (docs/12-backend.md
section 4, docs/09-architecture.md "Controlled storage").

Client filenames are never trusted or used as a path (SEC-01). Storage names
are server-generated from the dataset id.
"""

from __future__ import annotations

import uuid
from pathlib import Path


class DatasetStorage:
    def __init__(self, base_path: str) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save_raw_upload(self, dataset_id: uuid.UUID, raw_bytes: bytes) -> str:
        target = self._base_path / f"{dataset_id}.raw.csv"
        target.write_bytes(raw_bytes)
        return str(target)


class ReportStorage:
    def __init__(self, base_path: str) -> None:
        self._base_path = Path(base_path) / "reports"
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save_pdf(self, report_id: uuid.UUID, pdf_bytes: bytes) -> str:
        target = self._base_path / f"{report_id}.pdf"
        target.write_bytes(pdf_bytes)
        return str(target)

    def read_pdf(self, storage_ref: str) -> bytes:
        return Path(storage_ref).read_bytes()

"""LangChain Document Loader for UnDatasIO."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, List, Optional, Sequence

import pandas as pd

from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader

try:
    from undatasio import UnDatasIO
except ImportError as err:
    msg = (
        "undatasio package not found. "
        "Please install it with `pip install undatasio`."
    )
    raise ImportError(msg) from err


class UnDatasIOLoader(BaseLoader):
    """Load parsed text from UnDatasIO API (PDF / image / OCR)."""

    def __init__(
        self,
        token: str,
        file_path: Optional[str] = None,
        workspace_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> None:
        """Initialize loader.

        Args:
            token: UnDatasIO API access token.
            file_path: Single file to upload & parse (optional).
            workspace_id: Target workspace (optional).
            task_id: Target task (optional).
        """
        self.client = UnDatasIO(token=token)
        self.file_path = file_path
        self.workspace_id = workspace_id
        self.task_id = task_id

    # ------------------------------------------------------------------
    #  API  helper
    # ------------------------------------------------------------------
    def list_workspaces(self) -> List[dict[str, Any]]:
        """Return all workspaces."""
        return self.client.workspace_list()

    def list_tasks(self, workspace_id: str) -> List[dict[str, Any]]:
        """Return all tasks in a workspace."""
        return self.client.task_list(work_id=workspace_id)

    def list_files(self, task_id: Optional[str] = None) -> List[dict[str, Any]]:
        """List all files in a task."""
        tid = task_id or self._get_or_pick_task(self._get_or_pick_workspace())
        return self.client.get_task_files(task_id=tid)

    def upload_file(
        self, file_path: str, task_id: Optional[str] = None
    ) -> bool:
        """Upload single file."""
        tid = task_id or self._get_or_pick_task(self._get_or_pick_workspace())
        return self.client.upload_file(task_id=tid, file_path=file_path)

    def upload_files(
        self, file_paths: Sequence[str], task_id: Optional[str] = None
    ) -> List[bool]:
        """Batch upload."""
        return [self.upload_file(p, task_id) for p in file_paths]

    def parse_files(
        self, file_ids: List[str], task_id: Optional[str] = None
    ) -> bool:
        """Trigger parsing for specified file IDs."""
        tid = task_id or self._get_or_pick_task(self._get_or_pick_workspace())
        return self.client.parse_files(task_id=tid, file_ids=file_ids)

    def wait_for_parse(
        self, file_ids: List[str], task_id: Optional[str] = None, poll: int = 5
    ) -> None:
        """Poll until all files reach 'parser success'."""
        tid = task_id or self._get_or_pick_task(self._get_or_pick_workspace())
        while True:
            time.sleep(poll)
            task_files = pd.DataFrame(self.client.get_task_files(task_id=tid))
            status_series = (
                task_files.loc[task_files["file_id"].isin(file_ids), "status"]
                .dropna()
                .unique()
            )
            if all(s == "parser success" for s in status_series):
                return
            if any(s in ("parser failed", "error") for s in status_series):
                msg = "Parsing failed"
                raise RuntimeError(msg)

    def get_parse_result(
        self, file_id: str, task_id: Optional[str] = None
    ) -> str:
        """Return parsed text for a single file."""
        tid = task_id or self._get_or_pick_task(self._get_or_pick_workspace())
        lines: List[str] = self.client.get_parse_result(
            task_id=tid, file_id=file_id
        )
        return "\n".join(lines)

    def get_parse_results(
        self, file_ids: List[str], task_id: Optional[str] = None
    ) -> List[Document]:
        """Return List[Document] for multiple file IDs."""
        tid = task_id or self._get_or_pick_task(self._get_or_pick_workspace())
        docs: List[Document] = []
        for fid in file_ids:
            text = self.get_parse_result(fid, task_id=tid)
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": fid, "task_id": tid},
                )
            )
        return docs

    # ------------------------------------------------------------------
    #  一键加载（兼容单文件）
    # ------------------------------------------------------------------
    def load(self) -> List[Document]:
        """Upload -> parse -> return Document (single-file mode)."""
        if not self.file_path:
            msg = "file_path required for load()"
            raise ValueError(msg)

        task_id = self._get_or_pick_task(self._get_or_pick_workspace())
        if not self.upload_file(self.file_path, task_id):
            msg = "Upload failed"
            raise RuntimeError(msg)

        files = self.list_files(task_id)
        file_id = next(
            f["file_id"]
            for f in files
            if f["file_name"] == Path(self.file_path).name
        )

        if not self.parse_files([file_id], task_id):
            msg = "Parse trigger failed"
            raise RuntimeError(msg)

        self.wait_for_parse([file_id], task_id)
        return self.get_parse_results([file_id], task_id)

    # -------------------- 内部辅助 --------------------
    def _get_or_pick_workspace(self) -> str:
        if self.workspace_id:
            return self.workspace_id
        ws = self.list_workspaces()
        if not ws:
            msg = "No workspace found"
            raise RuntimeError(msg)
        return ws[0]["work_id"]

    def _get_or_pick_task(self, work_id: str) -> str:
        if self.task_id:
            return self.task_id
        ts = self.list_tasks(work_id)
        if not ts:
            msg = "No task found"
            raise RuntimeError(msg)
        return ts[0]["task_id"]
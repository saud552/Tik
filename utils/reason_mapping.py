import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any


@dataclass
class MappingSource:
    path: Path
    last_loaded_ts: float


class ReasonMapping:
    """
    Loads external mapping from dynamic reason IDs (strings from UI/schema)
    to numeric TikTok reasons used by the reporter. Supports reload and validation.
    """

    def __init__(self, mapping_path: Path):
        self._path = mapping_path
        self._id_to_reason: Dict[str, int] = {}
        self._loaded = False

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> None:
        if not self._path.exists():
            self._id_to_reason = {}
            self._loaded = True
            return
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Expect structure: { "video": { "id_string": 1001, ... }, "account": { ... } }
        # Store flattened with keys like "video:harassment_bullying" -> 1003
        flattened: Dict[str, int] = {}
        if isinstance(data, dict):
            for scope, items in data.items():
                if not isinstance(items, dict):
                    continue
                for k, v in items.items():
                    try:
                        flattened[f"{scope}:{k}"] = int(v)
                    except Exception:
                        continue
        self._id_to_reason = flattened
        self._loaded = True

    def reload(self) -> None:
        self._loaded = False
        self.load()

    def resolve(self, scope: str, dynamic_id: str) -> Optional[int]:
        if not self._loaded:
            self.load()
        return self._id_to_reason.get(f"{scope}:{dynamic_id}")

    def has(self, scope: str, dynamic_id: str) -> bool:
        if not self._loaded:
            self.load()
        return f"{scope}:{dynamic_id}" in self._id_to_reason


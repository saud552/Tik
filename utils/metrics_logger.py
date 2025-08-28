import json
import time
from pathlib import Path
from typing import Dict


_METRICS_FILE = Path("data/report_metrics.json")


def _read_metrics() -> Dict[str, int]:
    if not _METRICS_FILE.exists():
        return {
            "video_success": 0,
            "video_fail": 0,
            "account_success": 0,
            "account_fail": 0,
            "last_update": int(time.time()),
        }
    try:
        return json.loads(_METRICS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "video_success": 0,
            "video_fail": 0,
            "account_success": 0,
            "account_fail": 0,
            "last_update": int(time.time()),
        }


def _write_metrics(data: Dict[str, int]) -> None:
    _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["last_update"] = int(time.time())
    _METRICS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def incr(key: str, amount: int = 1) -> None:
    data = _read_metrics()
    data[key] = int(data.get(key, 0)) + amount
    _write_metrics(data)


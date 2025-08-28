# Utility modules for TikTok Reporting Bot

try:
    from .reason_mapping import ReasonMapping  # noqa: F401
except Exception:
    # optional import; mapping loader may not be needed in some contexts
    ReasonMapping = None  # type: ignore
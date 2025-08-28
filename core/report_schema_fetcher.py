import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import os

from playwright.async_api import async_playwright


@dataclass
class ReportSchema:
    source: str  # 'web' or 'fallback'
    categories: List[Dict[str, Any]]


async def _extract_from_html(html: str) -> Optional[ReportSchema]:
    """محاولة استخراج بنية الفئات/الأسباب من HTML إن وُجدت (best-effort)."""
    # لا توجد صيغة موثقة، نحاول SIGI_STATE أو أنماط معقولة
    m = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', html)
    if m:
        try:
            data = json.loads(m.group(1))
            # لا يوجد مكان واضح لأسباب البلاغ، نحاول fallback فورًا
            return None
        except Exception:
            return None
    return None


_CACHE_DIR = Path("data")
_CACHE_FILE = _CACHE_DIR / "report_schema_cache.json"
_DEFAULT_TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _read_cache() -> Dict[str, Any]:
    try:
        if not _CACHE_FILE.exists():
            return {}
        with _CACHE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_cache(cache: Dict[str, Any]) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with _CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _get_cached_schema(report_type: str, ttl_seconds: Optional[int]) -> Optional[ReportSchema]:
    cache = _read_cache()
    entry = cache.get(report_type)
    if not entry:
        return None
    try:
        ts = float(entry.get("timestamp", 0))
        if ttl_seconds is None:
            ttl_seconds = _DEFAULT_TTL_SECONDS
        if (time.time() - ts) > ttl_seconds:
            return None
        categories = entry.get("categories") or []
        if not isinstance(categories, list):
            return None
        return ReportSchema(source="cache", categories=categories)
    except Exception:
        return None


def _store_schema_in_cache(report_type: str, categories: List[Dict[str, Any]]) -> None:
    cache = _read_cache()
    cache[report_type] = {
        "timestamp": time.time(),
        "categories": categories,
    }
    _write_cache(cache)


async def fetch_report_schema(report_type: str, target_url: Optional[str] = None, locale: str = "en-US", *, use_cache: bool = True, ttl_seconds: Optional[int] = None, force_refresh: bool = False) -> ReportSchema:
    """
    يجلب فئات/أنواع البلاغ من واجهة تيك توك إن أمكن؛ وإلا يرجع fallback.
    report_type: 'video' أو 'account'
    """
    # 1) محاولة استخدام الكاش
    if use_cache and not force_refresh:
        cached = _get_cached_schema(report_type, ttl_seconds)
        if cached:
            return cached

    # 2) محاولة فتح الصفحة ذات الصلة
    if target_url:
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(locale=locale)
            page = await context.new_page()
            await page.goto(target_url, wait_until="networkidle")
            html = await page.content()
            await context.close()
            await browser.close()
            await pw.stop()
            schema = await _extract_from_html(html)
            if schema:
                # تخزين في الكاش
                _store_schema_in_cache(report_type, schema.categories)
                return schema
        except Exception:
            pass

    # 3) Fallback منظم (نصي)، يستخدم كنصوص فقط لإرسالها ضمن report_desc
    if report_type == "video":
        categories = [
            {
                "key": "harassment",
                "title": "تحرش وإساءة",
                "items": [
                    {"id": "harassment_bullying", "title": "تحرش/تنمر"},
                    {"id": "hate_speech", "title": "خطاب كراهية"},
                ],
            },
            {
                "key": "violence",
                "title": "عنف وإيذاء",
                "items": [
                    {"id": "graphic_violence", "title": "عنف صريح"},
                    {"id": "dangerous_acts", "title": "سلوك خطير"},
                ],
            },
            {
                "key": "sexual",
                "title": "محتوى جنسي",
                "items": [
                    {"id": "nudity", "title": "عري/إيحاء جنسي"},
                    {"id": "minor_safety", "title": "سلامة القُصّر"},
                ],
            },
            {
                "key": "misinfo",
                "title": "معلومات مضللة",
                "items": [
                    {"id": "health_misinfo", "title": "صحي/طبي"},
                    {"id": "general_misinfo", "title": "عامة"},
                ],
            },
            {
                "key": "other",
                "title": "أخرى",
                "items": [
                    {"id": "other", "title": "سبب آخر (وصف نصي)"},
                ],
            },
        ]
    else:
        categories = [
            {
                "key": "spam",
                "title": "رسائل مزعجة/احتيال",
                "items": [
                    {"id": "spam_ads", "title": "إعلانات مزعجة"},
                    {"id": "scam_fraud", "title": "احتيال"},
                ],
            },
            {
                "key": "impersonation",
                "title": "انتحال شخصية",
                "items": [
                    {"id": "impersonation_user", "title": "يدّعي أنه شخص/كيان آخر"},
                ],
            },
            {
                "key": "abuse",
                "title": "تحرش وإساءة",
                "items": [
                    {"id": "harassment", "title": "تحرش/تنمر"},
                ],
            },
            {
                "key": "other",
                "title": "أخرى",
                "items": [
                    {"id": "other", "title": "سبب آخر (وصف نصي)"},
                ],
            },
        ]

    # تخزين fallback في الكاش لتحسين الأداء، مع تمييز المصدر
    _store_schema_in_cache(report_type, categories)
    return ReportSchema(source="fallback", categories=categories)


async def refresh_report_schema(report_type: str, target_url: Optional[str] = None, locale: str = "en-US") -> ReportSchema:
    """تحديث قسري للكاش وإرجاع المخطط الأحدث المتاح."""
    return await fetch_report_schema(report_type, target_url, locale, use_cache=True, force_refresh=True)


import asyncio
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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


async def fetch_report_schema(report_type: str, target_url: Optional[str] = None, locale: str = "en-US") -> ReportSchema:
    """
    يجلب فئات/أنواع البلاغ من واجهة تيك توك إن أمكن؛ وإلا يرجع fallback.
    report_type: 'video' أو 'account'
    """
    # محاولة فتح الصفحة ذات الصلة
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
                return schema
        except Exception:
            pass

    # Fallback منظم (نصي)، يستخدم كنصوص فقط لإرسالها ضمن report_desc
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

    return ReportSchema(source="fallback", categories=categories)


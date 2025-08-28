#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تشغيل مهمة بلاغ حساب TikTok يدويًا باستخدام المكونات الإنتاجية.

الخطوات:
- تحميل الحسابات من accounts.json
- تهيئة ReportScheduler
- إضافة مهمة بلاغ لنوع الحساب target_username مع سبب محدد
- الانتظار حتى انتهاء التنفيذ ثم طباعة ملخص النتائج
"""

import asyncio
import time
from typing import Optional

from core.account_manager import TikTokAccountManager
from core.report_scheduler import ReportScheduler
from models.job import ReportType, ReportJob, JobStatus


async def run_account_report(
    target_username: str,
    reason_code: int,
    reports_per_account: int = 1,
) -> Optional[ReportJob]:
    """يشغّل مهمة بلاغ حساب ويعيد المهمة المكتملة عند الانتهاء إن وُجدت."""
    account_manager = TikTokAccountManager("accounts.json")
    scheduler = ReportScheduler(account_manager)

    # جدولة المهمة
    job_id = await scheduler.queue_job(
        report_type=ReportType.ACCOUNT,
        target=target_username,
        reason=reason_code,
        reports_per_account=reports_per_account,
        socks5_proxies=None,
    )

    # الانتظار حتى انتهاء المعالجة مع التحقق من اكتمال المهمة
    deadline = time.time() + 300  # 5 دقائق
    while time.time() < deadline:
        # تحقق من الاكتمال
        for job in scheduler.get_recent_jobs(limit=10):
            if job.id == job_id:
                return job

        # إذا لم تعد هناك معالجة أو لم تعد المهمة نشطة/بالطابور، اخرج
        in_active = job_id in scheduler.active_jobs
        in_queue = any(j.id == job_id for j in scheduler.job_queue)
        if not scheduler.is_running and not in_active and not in_queue:
            break

        await asyncio.sleep(0.5)

    # محاولة أخيرة للحصول على المهمة بعد الخروج من الحلقة
    for job in scheduler.get_recent_jobs(limit=10):
        if job.id == job_id:
            return job
    return None


async def main():
    # الهدف: حساب TikTok
    target_url_or_username = "saoud46474"
    # اختيار سبب حقيقي من إعدادات الحسابات (spam)
    reason_code = 1019
    reports_per_account = 1

    print("🚀 بدء مهمة البلاغ عن الحساب",
          f"target={target_url_or_username} reason={reason_code} rpa={reports_per_account}")

    job = await run_account_report(
        target_username=target_url_or_username,
        reason_code=reason_code,
        reports_per_account=reports_per_account,
    )

    if not job:
        print("❌ لم يتم العثور على نتيجة المهمة بعد التنفيذ")
        return

    print("\n📋 نتيجة المهمة:")
    print(f"🆔 id: {job.id}")
    print(f"📝 type: {job.report_type.value}")
    print(f"🎯 target: {job.target}")
    print(f"🚨 reason: {job.reason}")
    print(f"🔢 per_account: {job.reports_per_account}")
    print(f"📊 total_reports: {job.total_reports}")
    print(f"✅ successful: {job.successful_reports}")
    print(f"❌ failed: {job.failed_reports}")
    print(f"📌 status: {job.status.value}")
    if job.status == JobStatus.FAILED and job.error_message:
        print(f"⚠️ error: {job.error_message}")


if __name__ == "__main__":
    asyncio.run(main())


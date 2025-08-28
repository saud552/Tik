#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تشغيل بلاغ حساب عبر مسار الويب فقط:
- استخدام Playwright (non-headless) عبر Xvfb لفتح جلسة وتحصيل الكوكيز
- استخراج user_id من صفحة الويب
- إرسال البلاغ عبر Web API
"""

import asyncio
import re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

from core.account_manager import TikTokAccountManager
from core.tiktok_reporter import TikTokReporter
from core.web_login_automator import TikTokWebLoginAutomator


def extract_username_from_input(target: str) -> str:
    target = target.strip()
    if target.startswith('@'):
        return target[1:]
    if target.startswith('http://') or target.startswith('https://'):
        try:
            parsed = urlparse(target)
            # أنماط شائعة: /@username/...
            m = re.search(r'/@([^/]+)', parsed.path)
            if m:
                return m.group(1)
        except Exception:
            pass
    # fallback: اعتبرها اسم مستخدم خام
    return target


async def main():
    # مدخلات مهمة البلاغ
    target_input = "https://www.tiktok.com/@saoud46474?_t=ZS-8z50Fdwsy5B&_r=1"
    reason_code = 1019  # spam

    username = extract_username_from_input(target_input)
    print(f"🎯 الهدف (username): {username}")

    # احصل على أول حساب سليم
    manager = TikTokAccountManager("accounts.json")
    accounts = manager.get_healthy_accounts()
    if not accounts:
        print("❌ لا توجد حسابات سليمة متاحة")
        return
    account = accounts[0]
    password_plain = manager.get_decrypted_password(account.id)
    if not password_plain:
        print("❌ تعذر فك تشفير كلمة مرور الحساب")
        return

    print(f"👤 استخدام الحساب: {account.username}")

    # 1) تسجيل دخول ويب non-headless (عبر Xvfb إذا لزم)
    automator = TikTokWebLoginAutomator(headless=False)
    cookies_dict = await automator.login_and_get_cookies(account.username, password_plain, proxy=account.proxy)
    if not cookies_dict:
        print("❌ فشل تسجيل دخول الويب عبر Playwright وعدم الحصول على كوكيز")
        return

    # 2) بناء Reporter وتحميل الكوكيز
    reporter = TikTokReporter(manager)
    for k, v in cookies_dict.items():
        reporter.session.cookies.set(k, v)
    cookies_str = '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])
    manager.update_account_cookies(account.id, cookies_str)
    print("✅ كوكيز الويب محملة في الجلسة")

    # 3) استخراج user_id عبر الويب فقط باستخدام Playwright مباشرةً
    async def get_user_id_via_playwright(user: str, cookies: dict[str, str]) -> str | None:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="UTC",
            viewport={"width": 1366, "height": 850},
        )
        # حقن الكوكيز
        cookie_list = []
        for k, v in cookies.items():
            if not k or v is None:
                continue
            cookie_list.append({
                "name": k,
                "value": v,
                "domain": ".tiktok.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
            })
        if cookie_list:
            await context.add_cookies(cookie_list)

        page = await context.new_page()
        try:
            await page.goto(f"https://www.tiktok.com/@{user}", wait_until="networkidle")
            html = await page.content()
            # 1) meta al:ios:url
            m = re.search(r'<meta[^>]+content="tiktok://user/(\d+)"', html)
            if m:
                return m.group(1)
            # 2) "id":"123456"
            m = re.search(r'"id":"(\d+)"', html)
            if m:
                return m.group(1)
            # 3) SIGI_STATE
            m = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', html)
            if m:
                j = m.group(1)
                mm = re.search(r'"id":"(\d+)"', j)
                if mm:
                    return mm.group(1)
            return None
        finally:
            try:
                await context.close()
            except Exception:
                pass
            try:
                await browser.close()
            except Exception:
                pass
            try:
                await pw.stop()
            except Exception:
                pass

    target_user_id = await get_user_id_via_playwright(username, cookies_dict)
    if not target_user_id:
        print("❌ تعذر استخراج user_id من صفحة المستخدم عبر Playwright")
        return
    print(f"🆔 user_id: {target_user_id}")

    # 4) إرسال البلاغ عبر Web API فقط
    success = await reporter._report_account_web(target_user_id, reason_code)
    if success:
        print("🎉 تم إرسال البلاغ بنجاح عبر Web API")
    else:
        print("❌ فشل إرسال البلاغ عبر Web API")


if __name__ == "__main__":
    asyncio.run(main())


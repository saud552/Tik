import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright


class TikTokWebLoginAutomator:
	"""تسجيل دخول ويب لاستخراج كوكيز جلسة TikTok باستخدام Playwright"""

	def __init__(self, headless: bool = True):
		self.headless = headless

	async def login_and_get_cookies(self, username: str, password: str, proxy: Optional[str] = None) -> Dict[str, str]:
		"""يسجّل الدخول ويعيد قاموس كوكيز مثل ttwid, tt_csrf_token, sessionid إن توفّرت"""
		cookies: Dict[str, str] = {}
		playwright = await async_playwright().start()
		browser = None
		context = None
		page = None
		try:
			launch_args = {"headless": self.headless}
			# تمرير البروكسي إن وُجد (Playwright يدعم http/socks5)
			if proxy:
				launch_args["proxy"] = {"server": proxy}
			browser = await playwright.chromium.launch(**launch_args)
			# إعدادات سياق أقرب إلى متصفح حقيقي
			context = await browser.new_context(
				user_agent=(
					"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
					"(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
				),
				locale="en-US",
				timezone_id="UTC",
				viewport={"width": 1366, "height": 850},
			)
			page = await context.new_page()

			# الانتقال إلى الصفحة الرئيسية أولاً لقبول ملف تعريف الارتباط إن وُجد
			await page.goto("https://www.tiktok.com/", wait_until="load")
			# قبول سياسة الكوكيز إن ظهرت
			for selector in [
				"button:has-text('Accept all')",
				"text=Accept all",
				"[data-e2e='cookies-banner-accept']",
			]:
				try:
					await page.click(selector, timeout=3000)
					break
				except Exception:
					pass

			# الانتقال مباشرة إلى نموذج البريد/اسم المستخدم
			await page.goto("https://www.tiktok.com/login/phone-or-email/email", wait_until="networkidle")

			# محاولات متعددة لملء الحقول على الصفحة أو داخل iframes
			selectors_user = ["input[name='username']", "input[name='email']", "input[type='text']"]
			selectors_pass = ["input[name='password']", "input[type='password']"]
			selectors_submit = ["button[type='submit']", "button:has-text('Log in')"]

			async def try_fill_in(target_page):
				for su in selectors_user:
					try:
						await target_page.fill(su, username, timeout=3000)
						break
					except Exception:
						continue
				for sp in selectors_pass:
					try:
						await target_page.fill(sp, password, timeout=3000)
						break
					except Exception:
						continue
				for sb in selectors_submit:
					try:
						await target_page.click(sb, timeout=3000)
						return True
					except Exception:
						continue
				# محاولة إرسال Enter
				try:
					await target_page.keyboard.press("Enter")
					return True
				except Exception:
					return False

			ok = await try_fill_in(page)
			if not ok:
				# تجربة البحث داخل أي إطار
				for fr in page.frames:
					try:
						ok = await try_fill_in(fr)
						if ok:
							break
					except Exception:
						pass

			# الانتظار لإتمام التحويل أو ظهور الصفحة الرئيسية
			await page.wait_for_load_state("networkidle")
			# مهلة قصيرة لالتقاط الكوكيز بعد المصادقة
			await page.wait_for_timeout(2000)

			# جلب الكوكيز من السياق
			all_cookies = await context.cookies()
			for c in all_cookies:
				name = c.get("name")
				value = c.get("value")
				if name and value:
					cookies[name] = value

			return cookies
		finally:
			try:
				if context:
					await context.close()
			except Exception:
				pass
			try:
				if browser:
					await browser.close()
			except Exception:
				pass
			try:
				await playwright.stop()
			except Exception:
				pass


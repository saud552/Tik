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
			if proxy:
				launch_args["proxy"] = {"server": proxy}
			browser = await playwright.chromium.launch(**launch_args)
			context = await browser.new_context()
			page = await context.new_page()

			# الانتقال إلى صفحة تسجيل الدخول
			await page.goto("https://www.tiktok.com/login", wait_until="load")

			# قد يعرض تيك توك عدة مزودين لتسجيل الدخول، نحاول حقل اسم المستخدم/كلمة المرور إن وُجد
			# ملاحظة: محددات العناصر قد تتغير مع الزمن؛ نستخدم محددات عامة وننتظر ظهورها
			# محاولة النقر على تبويب "Use phone / email / username" إذا ظهر
			try:
				await page.click("text=Use phone / email / username", timeout=5000)
			except Exception:
				pass

			# اختيار تبويب "Email / Username" إن وُجد
			try:
				await page.click("text=Email / Username", timeout=5000)
			except Exception:
				pass

			# تعبئة الحقول
			await page.fill("input[name='username'], input[type='text']", username, timeout=15000)
			await page.fill("input[name='password'], input[type='password']", password, timeout=15000)

			# النقر على زر تسجيل الدخول
			# أزرار محتملة: "Log in" أو زر ضمن form
			try:
				await page.click("button:has-text('Log in')", timeout=10000)
			except Exception:
				# محاولة إرسال النموذج عبر Enter
				await page.keyboard.press("Enter")

			# الانتظار لإتمام التحويل أو ظهور الصفحة الرئيسية
			await page.wait_for_load_state("networkidle")

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


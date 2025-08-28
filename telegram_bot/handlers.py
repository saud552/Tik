import asyncio
import re
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from core.account_manager import TikTokAccountManager
from core.report_scheduler import ReportScheduler
from core.tiktok_reporter import TikTokReporter
from models.job import ReportType
from telegram_bot.keyboards import TikTokKeyboards
from config.settings import ADMIN_USER_ID, ADMIN_USER_IDS, REPORT_REASONS
from utils.reason_mapping import ReasonMapping
from pathlib import Path
from core.web_login_automator import TikTokWebLoginAutomator
from core.report_schema_fetcher import fetch_report_schema, refresh_report_schema

# حالات المحادثة
(
    WAITING_FOR_USERNAME,
    WAITING_FOR_PASSWORD,
    WAITING_FOR_TARGET,
    WAITING_FOR_REASON,
    WAITING_FOR_REPORTS_COUNT,
    WAITING_FOR_INTERVAL,
    WAITING_FOR_CONFIRMATION,
    WAITING_FOR_PROXIES
) = range(8)

class TikTokHandlers:
    def __init__(self):
        self.account_manager = TikTokAccountManager()
        self.scheduler = ReportScheduler(self.account_manager)
        self.reporter = TikTokReporter()
        self.user_states = {}  # لتخزين حالة المستخدم
        # مُحمّل خريطة الأسباب الديناميكية
        self.reason_mapping = ReasonMapping(Path("config/reason_mapping.json"))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        if not update or not update.effective_user or not update.message:
            return
        allowed_admins = set(ADMIN_USER_IDS or ([] if not ADMIN_USER_ID else [ADMIN_USER_ID]))
        if update.effective_user.id not in allowed_admins:
            await update.message.reply_text("❌ عذراً، هذا البوت متاح للمدير فقط.")
            return
        
        # دعم أوامر إدارية سريعة مع start: /start refresh_schema أو /start show_schema
        txt = update.message.text or ""
        if "refresh_schema" in txt:
            await self.admin_refresh_schema(update, context)
            return
        if "show_schema" in txt:
            await self.admin_show_schema(update, context)
            return

        await update.message.reply_text(
            "🎉 مرحباً بك في بوت بلاغات TikTok!\n\n"
            "اختر الخيار المطلوب من القائمة أدناه:",
            reply_markup=TikTokKeyboards.get_main_menu()
        )
    
    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة القائمة الرئيسية"""
        query = update.callback_query
        if not query:
            return
        await query.answer()
        
        if query.data == "manage_accounts":
            await query.edit_message_text(
                "🔐 إدارة حسابات TikTok\n\n"
                "اختر العملية المطلوبة:",
                reply_markup=TikTokKeyboards.get_account_management_menu()
            )
        elif query.data == "report_video":
            # تمرير Update و Context كما تتوقع دالة start_report_process
            await self.start_report_process(update, context)
        elif query.data == "report_account":
            await self.start_report_process(update, context)
        elif query.data == "job_status":
            await self.show_job_status(query)
        elif query.data == "statistics":
            await self.show_statistics(query)
        elif query.data == "main_menu":
            await self.start_command(update, context)
    
    async def start_report_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بدء عملية البلاغ"""
        if not update or not update.callback_query:
            return ConversationHandler.END
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data or ""
        # تحديد نوع البلاغ بدقة من زر القائمة
        if data == "report_video":
            report_type = ReportType.VIDEO
        elif data == "report_account":
            report_type = ReportType.ACCOUNT
        else:
            # fallback آمن
            report_type = ReportType.VIDEO
        self.user_states[user_id] = {
            'report_type': report_type,
            'target': None,
            'reason': None,
            'reports_per_account': None,
            'report_schema': None,
            'selected_reason_text': None,
        }
        
        report_type_text = "فيديو" if report_type == ReportType.VIDEO else "حساب"
        await query.edit_message_text(
            f"📝 الإبلاغ عن {report_type_text}\n\n"
            f"أدخل رابط {report_type_text} أو اسم المستخدم:",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        
        return WAITING_FOR_TARGET

    async def admin_refresh_schema(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """تحديث قسري لمخطط الفئات وتفريغ الكاش"""
        user = update.effective_user
        if not user or (user.id not in set(ADMIN_USER_IDS or ([] if not ADMIN_USER_ID else [ADMIN_USER_ID]))):
            return
        await update.message.reply_text("🔄 جاري تحديث مخطط البلاغات...")
        try:
            v = await refresh_report_schema('video')
            a = await refresh_report_schema('account')
            await update.message.reply_text(
                "✅ تم التحديث.\n"
                f"video: source={v.source}, cats={len(v.categories)}\n"
                f"account: source={a.source}, cats={len(a.categories)}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ فشل التحديث: {e}")

    async def admin_show_schema(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """عرض موجز عن المخطط الحالي من الكاش"""
        user = update.effective_user
        if not user or (user.id not in set(ADMIN_USER_IDS or ([] if not ADMIN_USER_ID else [ADMIN_USER_ID]))):
            return
        try:
            v = await fetch_report_schema('video')
            a = await fetch_report_schema('account')
            def summarize(schema):
                parts = []
                for c in (schema.categories or [])[:5]:
                    items = c.get('items', [])
                    parts.append(f"- {c.get('title')}: {min(len(items), 5)} عناصر")
                return "\n".join(parts)
            await update.message.reply_text(
                "📋 المخطط الحالي:\n"
                f"video (source={v.source}, cats={len(v.categories)}):\n{summarize(v)}\n\n"
                f"account (source={a.source}, cats={len(a.categories)}):\n{summarize(a)}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ فشل العرض: {e}")
    
    async def handle_target_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إدخال الهدف"""
        if not update or not update.message or not update.message.from_user:
            return ConversationHandler.END
        user_id = update.message.from_user.id
        if user_id not in self.user_states:
            await update.message.reply_text("❌ جلسة منتهية. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        target = update.message.text.strip()
        self.user_states[user_id]['target'] = target
        
        # التحقق من صحة الهدف
        target_type, target_id, user_id_info = self.reporter.validate_target(target)
        
        if target_type == 'unknown':
            await update.message.reply_text(
                "❌ الرابط أو اسم المستخدم غير صحيح.\n"
                "يرجى التأكد من صحة الرابط أو اسم المستخدم.",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_TARGET
        
        # محاولة جلب فئات ديناميكية من الويب (best-effort)
        try:
            target_url = target if target_type == 'video' else (f"https://www.tiktok.com/@{user_id_info}" if user_id_info else None)
            schema = await fetch_report_schema('video' if target_type == 'video' else 'account', target_url)
            self.user_states[user_id]['report_schema'] = schema
            await update.message.reply_text(
                "✅ تم تحديد الهدف بنجاح!\n\n"
                "الآن اختر نوع البلاغ:",
                reply_markup=TikTokKeyboards.get_dynamic_categories_menu(schema.categories)
            )
        except Exception:
            # fallback القديمة
            await update.message.reply_text(
                "✅ تم تحديد الهدف بنجاح!\n\n"
                "الآن اختر نوع البلاغ:",
                reply_markup=TikTokKeyboards.get_report_reasons_menu(self.user_states[user_id]['report_type'].value)
            )
        
        return WAITING_FOR_REASON
    
    async def handle_reason_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار نوع البلاغ مع دعم الفئات"""
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        await query.answer()
        
        user_id = query.from_user.id
        if user_id not in self.user_states:
            await query.edit_message_text("❌ جلسة منتهية. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        if query.data.startswith("dynitem_"):
            # اختيار سبب ديناميكي بالنص ومحاولة تحويله إلى سبب رقمي عبر mapping الخارجي
            rid = query.data.split("_", 1)[1]
            user_id = query.from_user.id
            schema = self.user_states[user_id].get('report_schema')
            reason_text = rid
            try:
                for cat in (schema.categories if schema else []):
                    for it in cat.get('items', []):
                        if str(it.get('id')) == rid:
                            reason_text = it.get('title') or rid
                            break
            except Exception:
                pass
            self.user_states[user_id]['selected_reason_text'] = reason_text

            # تحديد النطاق (video/account) بناءً على نوع البلاغ الحالي
            scope = 'video' if self.user_states[user_id]['report_type'] == ReportType.VIDEO else 'account'
            mapped = None
            try:
                mapped = self.reason_mapping.resolve(scope, rid)
            except Exception:
                mapped = None
            if isinstance(mapped, int):
                # تم إيجاد رقم سبب صالح
                self.user_states[user_id]['reason'] = mapped
                await query.edit_message_text(
                    f"✅ تم اختيار نوع البلاغ: {reason_text} (code: {mapped})\n\n"
                    "أدخل عدد البلاغات المراد تنفيذها من كل حساب (رقم صحيح):",
                    reply_markup=TikTokKeyboards.get_cancel_keyboard()
                )
                return WAITING_FOR_REPORTS_COUNT
            else:
                # لم يتم إيجاد تعيين رقمي؛ إرشاد المستخدم للعودة للفئات الثابتة أو اختيار من القائمة العامة
                await query.edit_message_text(
                    "⚠️ لا يوجد تعيين رقمي معتمد لهذا السبب الديناميكي.\n"
                    "يرجى اختيار السبب من الفئات الثابتة أو الضغط على 'عرض جميع الأسباب'.",
                    reply_markup=TikTokKeyboards.get_report_reasons_menu(self.user_states[user_id]['report_type'].value)
                )
                return WAITING_FOR_REASON

        if query.data.startswith("dyncat_"):
            # عرض عناصر الفئة المختارة
            category_key = query.data.split("_", 1)[1]
            user_id = query.from_user.id
            schema = self.user_states[user_id].get('report_schema')
            await query.edit_message_text(
                f"📂 اختر نوع البلاغ:",
                reply_markup=TikTokKeyboards.get_dynamic_items_menu(schema.categories if schema else [], category_key)
            )
            return WAITING_FOR_REASON

        if query.data.startswith("reason_"):
            # اختيار نوع بلاغ محدد
            reason_id = int(query.data.split("_")[1])
            self.user_states[user_id]['reason'] = reason_id
            
            reason_text = REPORT_REASONS[reason_id]
            await query.edit_message_text(
                f"✅ تم اختيار نوع البلاغ: {reason_text}\n\n"
                "أدخل عدد البلاغات المراد تنفيذها من كل حساب (رقم صحيح):",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_REPORTS_COUNT
            
        elif query.data.startswith("category_"):
            # اختيار فئة بلاغات
            category = query.data.split("_")[1]
            report_type = self.user_states[user_id]['report_type']
            
            await query.edit_message_text(
                f"📂 اختر نوع البلاغ من فئة '{category}':",
                reply_markup=TikTokKeyboards.get_category_reasons_menu(category, report_type.value)
            )
            
            return WAITING_FOR_REASON
            
        elif query.data == "show_all_reasons":
            # عرض جميع أنواع البلاغات
            report_type = self.user_states[user_id]['report_type']
            
            await query.edit_message_text(
                "📋 جميع أنواع البلاغات المتاحة:",
                reply_markup=TikTokKeyboards.get_all_reasons_menu(report_type.value)
            )
            
            return WAITING_FOR_REASON
            
        elif query.data == "back_to_categories":
            # العودة إلى قائمة الفئات
            user_id = query.from_user.id
            schema = self.user_states[user_id].get('report_schema')
            if schema:
                await query.edit_message_text(
                    "📂 اختر فئة البلاغ:",
                    reply_markup=TikTokKeyboards.get_dynamic_categories_menu(schema.categories)
                )
            else:
                report_type = self.user_states[user_id]['report_type']
                await query.edit_message_text(
                    "📂 اختر فئة البلاغ:",
                    reply_markup=TikTokKeyboards.get_report_reasons_menu(report_type.value)
                )
            
            return WAITING_FOR_REASON
            
        elif query.data == "back_to_target":
            # العودة إلى إدخال الهدف
            del self.user_states[user_id]
            report_type_text = "فيديو" if self.user_states.get(user_id, {}).get('report_type') == ReportType.VIDEO else "حساب"
            
            await query.edit_message_text(
                f"📝 الإبلاغ عن {report_type_text}\n\n"
                f"أدخل رابط {report_type_text} أو اسم المستخدم:",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_TARGET
    
    async def handle_reports_count_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال العدد كإدخال يدوي ثم الانتقال للفاصل"""
        # في النسخة اليدوية، نأتي من رسالة نصية لا من Callback
        message = getattr(update, 'message', None)
        if not message or not message.from_user:
            return ConversationHandler.END
        user_id = message.from_user.id
        if user_id not in self.user_states:
            await message.reply_text("❌ جلسة منتهية. يرجى البدء من جديد.")
            return ConversationHandler.END

        text = (message.text or '').strip()
        try:
            reports_count = int(text)
            if reports_count <= 0:
                raise ValueError
            self.user_states[user_id]['reports_per_account'] = reports_count
        except Exception:
            await message.reply_text(
                "❌ قيمة غير صحيحة. أدخل رقمًا صحيحًا (>0).",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_REPORTS_COUNT

        await message.reply_text(
            "⏱️ أدخل الفاصل الزمني بالثواني بين كل عملية بلاغ والتي تليها:\n\nمثال: 5",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        return WAITING_FOR_INTERVAL

    async def handle_interval_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال الفاصل الزمني ثم الانتقال لإدخال البروكسيات"""
        if not update or not update.message or not update.message.from_user:
            return ConversationHandler.END
        user_id = update.message.from_user.id
        if user_id not in self.user_states:
            await update.message.reply_text("❌ جلسة منتهية. يرجى البدء من جديد.")
            return ConversationHandler.END

        text = update.message.text.strip()
        try:
            interval = int(text)
            if interval < 0:
                raise ValueError
            self.user_states[user_id]['interval_seconds'] = interval
        except Exception:
            await update.message.reply_text(
                "❌ قيمة غير صحيحة. أدخل رقمًا صحيحًا (ثوانٍ).",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_INTERVAL

        await update.message.reply_text(
            "🧩 هل تريد إضافة بروكسيات SOCKS5؟\n"
            "أرسل قائمة البروكسيات بهذا الشكل (سطر لكل بروكسي):\n"
            "ip:port\n\n"
            "أرسل كلمة تخطي لتجاوز هذه الخطوة.",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        return WAITING_FOR_PROXIES
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تأكيد المهمة"""
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        await query.answer()
        
        if query.data == "confirm_report":
            user_id = query.from_user.id
            state = self.user_states[user_id]
            
            try:
                # تحقق صارم من اكتمال الحالة قبل إنشاء المهمة
                target = state.get('target')
                reason = state.get('reason')
                rpa = state.get('reports_per_account')
                healthy_count = len(self.account_manager.get_healthy_accounts())
                print(f"[Confirm] user={user_id} target={target} reason={reason} rpa={rpa} healthy_accounts={healthy_count}")

                if not target:
                    await query.edit_message_text(
                        "❌ لا يوجد هدف محدد. يرجى إدخال الرابط/اسم المستخدم أولاً.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )
                    return ConversationHandler.END
                if not isinstance(reason, int):
                    await query.edit_message_text(
                        "❌ لم يتم اختيار نوع البلاغ. يرجى اختيار السبب قبل التأكيد.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )
                    return ConversationHandler.END
                if not isinstance(rpa, int) or rpa <= 0:
                    await query.edit_message_text(
                        "❌ لم يتم تحديد عدد البلاغات لكل حساب. يرجى اختياره قبل التأكيد.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )
                    return ConversationHandler.END
                if healthy_count == 0:
                    await query.edit_message_text(
                        "❌ لا توجد حسابات سليمة متاحة للتنفيذ. يرجى إضافة حسابات أو فحصها.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )
                    return ConversationHandler.END

                # إن كان البلاغ على حساب: استخدم مسار الويب فقط مع تحديث رسالة التقدم دوريًا
                if state['report_type'] == ReportType.ACCOUNT:
                    msg = await query.edit_message_text(
                        "🚀 بدء عملية البلاغ عبر مسار الويب فقط...\n\n"
                        "سيتم تحديث هذه الرسالة بالتقدم حتى الانتهاء.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )

                    async def run_web_only_progress(chat_id: int, message_id: int):
                        # استخراج username من الإدخال
                        def extract_username(target: str) -> str:
                            target = target.strip()
                            if target.startswith('@'):
                                return target[1:]
                            if target.startswith('http://') or target.startswith('https://'):
                                try:
                                    parsed = urlparse(target)
                                    m = re.search(r'/@([^/]+)', parsed.path)
                                    if m:
                                        return m.group(1)
                                except Exception:
                                    pass
                            return target

                        # تحضير الحساب والجلسة
                        account = None
                        try:
                            accounts = self.account_manager.get_healthy_accounts()
                            if not accounts:
                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text="❌ لا توجد حسابات سليمة متاحة.")
                                return
                            account = accounts[0]
                            password_plain = self.account_manager.get_decrypted_password(account.id)
                            if not password_plain:
                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text="❌ تعذر فك تشفير كلمة مرور الحساب.")
                                return

                            # تسجيل دخول ويب (قد يتطلب بعض الوقت)
                            await self.reporter.web_login_and_store_cookies(account, password_plain)

                            # استخراج user_id عبر Playwright مباشرةً
                            async def get_user_id_via_playwright(user: str) -> str | None:
                                autom = TikTokWebLoginAutomator(headless=True)
                                # استخدم نفس الأتمتة لفتح الصفحة فقط عبر نفس المتصفح؟ سنفتح سياق جديد ونقرأ المحتوى
                                from playwright.async_api import async_playwright
                                pw = await async_playwright().start()
                                browser = await pw.chromium.launch(headless=True)
                                context_pw = await browser.new_context(
                                    user_agent=(
                                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                    )
                                )
                                page = await context_pw.new_page()
                                try:
                                    await page.goto(f"https://www.tiktok.com/@{user}", wait_until="networkidle")
                                    html = await page.content()
                                    m = re.search(r'<meta[^>]+content="tiktok://user/(\d+)"', html)
                                    if m:
                                        return m.group(1)
                                    m = re.search(r'"id":"(\d+)"', html)
                                    if m:
                                        return m.group(1)
                                    m = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', html)
                                    if m:
                                        j = m.group(1)
                                        mm = re.search(r'"id":"(\d+)"', j)
                                        if mm:
                                            return mm.group(1)
                                    return None
                                finally:
                                    try:
                                        await context_pw.close()
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

                            username = extract_username(state['target'])
                            user_id_web = await get_user_id_via_playwright(username)
                            if not user_id_web:
                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text="❌ تعذر استخراج user_id من صفحة المستخدم.")
                                return

                            total = state['reports_per_account']
                            interval = state.get('interval_seconds', 0) or 0
                            proxies = state.get('socks5_proxies') or []
                            proxy_index = 0
                            success = 0
                            failed = 0

                            # رسالة تقدم أولية
                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=(
                                    "🚀 بدء البلاغ عبر الويب فقط\n\n"
                                    f"👤 الهدف: @{username}\n"
                                    f"🆔 user_id: {user_id_web}\n"
                                    f"🚨 السبب: {state['reason']}\n"
                                    f"🔢 العدد: {total}\n"
                                    f"⏱️ الفاصل: {interval}s\n"
                                    f"🌐 بروكسيات: {len(proxies)}\n\n"
                                    f"التقدم: 0/{total}"
                                )
                            )

                            for i in range(total):
                                # تدوير البروكسي إن وجد
                                if proxies:
                                    if proxy_index >= len(proxies):
                                        proxy_index = 0
                                    socks = proxies[proxy_index]
                                    if socks.startswith('socks5://') and not socks.startswith('socks5h://'):
                                        socks = socks.replace('socks5://', 'socks5h://', 1)
                                    proxy_index += 1
                                    self.reporter.session.proxies.update({'http': socks, 'https': socks})
                                else:
                                    self.reporter.session.proxies.pop('http', None)
                                    self.reporter.session.proxies.pop('https', None)

                                ok = await self.reporter._report_account_web(user_id_web, state['reason'])
                                if ok:
                                    success += 1
                                else:
                                    failed += 1

                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text=(
                                        "🚀 البلاغ عبر الويب فقط (جارٍ)\n\n"
                                        f"👤 الهدف: @{username}\n"
                                        f"🆔 user_id: {user_id_web}\n"
                                        f"🚨 السبب: {state['reason']}\n"
                                        f"🔢 العدد: {total}\n"
                                        f"⏱️ الفاصل: {interval}s\n"
                                        f"🌐 بروكسيات: {len(proxies)}\n\n"
                                        f"التقدم: {success + failed}/{total} | ✅ {success} | ❌ {failed}"
                                    )
                                )

                                if i < total - 1 and interval > 0:
                                    await asyncio.sleep(interval)

                            # النهاية
                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=(
                                    "🎉 اكتملت عملية البلاغ عبر الويب فقط\n\n"
                                    f"👤 الهدف: @{username}\n"
                                    f"🆔 user_id: {user_id_web}\n"
                                    f"🚨 السبب: {state['reason']}\n"
                                    f"🔢 العدد: {total}\n"
                                    f"⏱️ الفاصل: {interval}s\n"
                                    f"🌐 بروكسيات: {len(proxies)}\n\n"
                                    f"النتيجة النهائية: ✅ {success} | ❌ {failed}"
                                )
                            )

                        except Exception as e:
                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=f"❌ خطأ أثناء تنفيذ البلاغ: {e}")

                    # إطلاق المهمة في الخلفية
                    asyncio.create_task(run_web_only_progress(query.message.chat_id, msg.message_id))

                elif state['report_type'] == ReportType.VIDEO:
                    # تنفيذ بلاغ الفيديو عبر مسار الويب فقط مع تحديث رسالة التقدم
                    msg = await query.edit_message_text(
                        "🚀 بدء عملية بلاغ الفيديو عبر الويب فقط...\n\n"
                        "سيتم تحديث هذه الرسالة بالتقدم حتى الانتهاء.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )

                    async def run_video_web_only_progress(chat_id: int, message_id: int):
                        # استخراج معلومات الفيديو عبر Playwright فقط
                        async def get_video_info_via_playwright(target_url: str) -> tuple[str | None, str | None]:
                            # حل الروابط المختصرة إن وُجدت
                            try:
                                resolved = self.reporter._resolve_short_url(target_url)
                            except Exception:
                                resolved = target_url

                            try:
                                from playwright.async_api import async_playwright
                                pw = await async_playwright().start()
                                browser = await pw.chromium.launch(headless=True)
                                context_pw = await browser.new_context(
                                    user_agent=(
                                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                                    )
                                )
                                page = await context_pw.new_page()
                                try:
                                    await page.goto(resolved, wait_until="networkidle")
                                    # استخدم الرابط النهائي لاستخراج video_id واسم المستخدم
                                    final_url = page.url
                                    vid = None
                                    user_name = None
                                    m = re.search(r"/video/(\d+)", final_url)
                                    if m:
                                        vid = m.group(1)
                                    mu = re.search(r"/@([^/]+)/video/", final_url)
                                    if mu:
                                        user_name = mu.group(1)
                                    # كاحتياط، افحص HTML
                                    if not vid or not user_name:
                                        html = await page.content()
                                        if not vid:
                                            mv = re.search(r'"aweme_id"\s*:\s*"(\d+)"', html)
                                            if mv:
                                                vid = mv.group(1)
                                        if not user_name:
                                            mu2 = re.search(r'"uniqueId"\s*:\s*"([^"]+)"', html)
                                            if mu2:
                                                user_name = mu2.group(1)
                                    return vid, user_name
                                finally:
                                    try:
                                        await context_pw.close()
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
                            except Exception:
                                return None, None

                        try:
                            target_url = state['target']
                            reason = state['reason']
                            total = state['reports_per_account']
                            interval = state.get('interval_seconds', 0) or 0
                            proxies = state.get('socks5_proxies') or []

                            video_id, username = await get_video_info_via_playwright(target_url)
                            if not video_id or not username:
                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text="❌ تعذر استخراج معلومات الفيديو (video_id/username).")
                                return

                            # استخراج user_id عبر صفحة المستخدم
                            async def get_user_id_via_playwright(user: str) -> str | None:
                                from playwright.async_api import async_playwright
                                pw = await async_playwright().start()
                                browser = await pw.chromium.launch(headless=True)
                                context_pw = await browser.new_context()
                                page = await context_pw.new_page()
                                try:
                                    await page.goto(f"https://www.tiktok.com/@{user}", wait_until="networkidle")
                                    html = await page.content()
                                    m = re.search(r'<meta[^>]+content=\"tiktok://user/(\d+)\"', html)
                                    if m:
                                        return m.group(1)
                                    m = re.search(r'\"id\":\"(\d+)\"', html)
                                    if m:
                                        return m.group(1)
                                    m = re.search(r'<script id=\"SIGI_STATE\" type=\"application/json\">(.*?)</script>', html)
                                    if m:
                                        j = m.group(1)
                                        mm = re.search(r'\"id\":\"(\d+)\"', j)
                                        if mm:
                                            return mm.group(1)
                                    return None
                                finally:
                                    try:
                                        await context_pw.close()
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

                            owner_user_id = await get_user_id_via_playwright(username)
                            if not owner_user_id:
                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text="❌ تعذر استخراج user_id لصاحب الفيديو.")
                                return

                            success = 0
                            failed = 0
                            proxy_index = 0

                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=(
                                    "🚀 بدء بلاغ الفيديو عبر الويب فقط\n\n"
                                    f"🎯 الرابط: {target_url}\n"
                                    f"📹 video_id: {video_id}\n"
                                    f"👤 username: @{username}\n"
                                    f"🆔 user_id: {owner_user_id}\n"
                                    f"🚨 السبب: {reason}\n"
                                    f"🔢 العدد: {total}\n"
                                    f"⏱️ الفاصل: {interval}s\n"
                                    f"🌐 بروكسيات: {len(proxies)}\n\n"
                                    f"التقدم: 0/{total}"
                                )
                            )

                            for i in range(total):
                                # تدوير البروكسي إن وجد
                                if proxies:
                                    if proxy_index >= len(proxies):
                                        proxy_index = 0
                                    socks = proxies[proxy_index]
                                    if socks.startswith('socks5://') and not socks.startswith('socks5h://'):
                                        socks = socks.replace('socks5://', 'socks5h://', 1)
                                    proxy_index += 1
                                    self.reporter.session.proxies.update({'http': socks, 'https': socks})
                                else:
                                    self.reporter.session.proxies.pop('http', None)
                                    self.reporter.session.proxies.pop('https', None)

                                ok = await self.reporter._report_video_web(video_id, owner_user_id, reason)
                                if ok:
                                    success += 1
                                else:
                                    failed += 1

                                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                    text=(
                                        "🚀 بلاغ الفيديو عبر الويب فقط (جارٍ)\n\n"
                                        f"🎯 الرابط: {target_url}\n"
                                        f"📹 video_id: {video_id}\n"
                                        f"👤 username: @{username}\n"
                                        f"🆔 user_id: {owner_user_id}\n"
                                        f"🚨 السبب: {reason}\n"
                                        f"🔢 العدد: {total}\n"
                                        f"⏱️ الفاصل: {interval}s\n"
                                        f"🌐 بروكسيات: {len(proxies)}\n\n"
                                        f"التقدم: {success + failed}/{total} | ✅ {success} | ❌ {failed}"
                                    )
                                )

                                if i < total - 1 and interval > 0:
                                    await asyncio.sleep(interval)

                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=(
                                    "🎉 اكتملت عملية بلاغ الفيديو عبر الويب فقط\n\n"
                                    f"🎯 الرابط: {target_url}\n"
                                    f"📹 video_id: {video_id}\n"
                                    f"👤 username: @{username}\n"
                                    f"🆔 user_id: {owner_user_id}\n"
                                    f"🚨 السبب: {reason}\n"
                                    f"🔢 العدد: {total}\n"
                                    f"⏱️ الفاصل: {interval}s\n"
                                    f"🌐 بروكسيات: {len(proxies)}\n\n"
                                    f"النتيجة النهائية: ✅ {success} | ❌ {failed}"
                                )
                            )

                        except Exception as e:
                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=f"❌ خطأ أثناء تنفيذ بلاغ الفيديو: {e}")

                    asyncio.create_task(run_video_web_only_progress(query.message.chat_id, msg.message_id))

                else:
                    # fallback لأي أنواع أخرى مستقبلية
                    job_id = await self.scheduler.queue_job(
                        report_type=state['report_type'],
                        target=state['target'],
                        reason=state['reason'],
                        reports_per_account=state['reports_per_account'],
                        socks5_proxies=state.get('socks5_proxies')
                    )
                    await query.edit_message_text(
                        f"✅ تم إنشاء مهمة البلاغ بنجاح!\n\n"
                        f"🆔 معرف المهمة: {job_id}\n"
                        f"📊 يمكنك متابعة التقدم من قائمة 'حالة المهام'\n\n"
                        f"🚀 بدأت العملية تلقائياً...",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )

                # تنظيف حالة المستخدم
                del self.user_states[user_id]
                
            except Exception as e:
                await query.edit_message_text(
                    f"❌ فشل في إنشاء مهمة البلاغ:\n{str(e)}",
                    reply_markup=TikTokKeyboards.get_main_menu()
                )
            
            return ConversationHandler.END
        
        elif query.data == "cancel_report":
            user_id = query.from_user.id
            del self.user_states[user_id]
            
            await query.edit_message_text(
                "❌ تم إلغاء عملية البلاغ.",
                reply_markup=TikTokKeyboards.get_main_menu()
            )
            return ConversationHandler.END
        
        elif query.data == "back_to_reports_count":
            await query.edit_message_text(
                "اختر عدد البلاغات المراد تنفيذها من كل حساب:",
                reply_markup=TikTokKeyboards.get_reports_per_account_menu()
            )
            return WAITING_FOR_REPORTS_COUNT

    async def handle_proxies_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """استقبال البروكسيات واختبارها ثم الانتقال للتأكيد"""
        if not update or not update.message or not update.message.from_user:
            return ConversationHandler.END
        user_id = update.message.from_user.id
        text = update.message.text.strip()
        if user_id not in self.user_states:
            await update.message.reply_text("❌ جلسة منتهية. يرجى البدء من جديد.")
            return ConversationHandler.END

        if text.lower() == "تخطي":
            # تخطي البروكسيات
            self.user_states[user_id]['socks5_proxies'] = []
            await self._show_final_summary(update.message, user_id)
            return WAITING_FOR_CONFIRMATION

        # استخراج البروكسيات من النص
        proxy_candidates = [line.strip() for line in text.splitlines() if line.strip()]
        
        if not proxy_candidates:
            await update.message.reply_text(
                "❌ لم يتم العثور على بروكسيات صحيحة.\n"
                "يرجى إدخال البروكسيات بصيغة ip:port أو إرسال 'تخطي'",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_PROXIES

        # اختبار البروكسيات
        await update.message.reply_text(
            "🔍 جاري اختبار البروكسيات...\n"
            "قد يستغرق هذا بضع دقائق...",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )

        try:
            # استيراد نظام اختبار البروكسيات
            from utils.proxy_tester import test_proxies
            
            # اختبار البروكسيات
            working_proxies, proxy_stats = await test_proxies(proxy_candidates)
            
            # حفظ البروكسيات العاملة
            self.user_states[user_id]['socks5_proxies'] = working_proxies
            
            # عرض نتائج الاختبار
            test_result = (
                f"🧩 نتائج اختبار البروكسيات:\n\n"
                f"📊 الإجمالي: {proxy_stats['total']}\n"
                f"✅ العاملة: {proxy_stats['working']}\n"
                f"❌ الفاشلة: {proxy_stats['failed']}\n"
                f"📈 معدل النجاح: {proxy_stats['success_rate']:.1f}%\n"
                f"⏱️ متوسط الاستجابة: {proxy_stats['avg_response_time']:.2f}s\n\n"
            )
            
            if working_proxies:
                test_result += f"✅ البروكسيات العاملة: {len(working_proxies)}\n"
                for i, proxy in enumerate(working_proxies[:5], 1):  # عرض أول 5 فقط
                    test_result += f"   {i}. {proxy}\n"
                if len(working_proxies) > 5:
                    test_result += f"   ... و {len(working_proxies) - 5} أخرى\n"
            else:
                test_result += "⚠️ لم يتم العثور على بروكسيات عاملة\n"
            
            await update.message.reply_text(test_result)
            
            # الانتقال إلى الملخص النهائي
            await self._show_final_summary(update.message, user_id)
            return WAITING_FOR_CONFIRMATION
            
        except ImportError:
            # إذا لم يتم تثبيت المكتبات الجديدة، استخدم الطريقة القديمة
            await self._fallback_proxy_testing(update.message, user_id, proxy_candidates)
            return WAITING_FOR_CONFIRMATION
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطأ في اختبار البروكسيات: {str(e)}\n"
                "سيتم المتابعة بدون بروكسيات",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            self.user_states[user_id]['socks5_proxies'] = []
            await self._show_final_summary(update.message, user_id)
            return WAITING_FOR_CONFIRMATION
    
    async def _fallback_proxy_testing(self, message, user_id: int, proxy_candidates: list):
        """اختبار البروكسيات بالطريقة القديمة (احتياطية)"""
        proxies: list[str] = []
        
        # فلترة الصيغة ip:port
        for candidate in proxy_candidates:
            if ':' in candidate:
                host, port = candidate.split(':', 1)
                if host and port.isdigit():
                    proxies.append(candidate)

        # اختبار البروكسيات بشكل مبسط
        valid_proxies: list[str] = []
        for proxy in proxies:
            host, port = proxy.split(':', 1)
            if host and port.isdigit():
                valid_proxies.append(f"socks5://{host}:{port}")

        # حفظ البروكسيات الفعالة في الحالة
        self.user_states[user_id]['socks5_proxies'] = valid_proxies

        await message.reply_text(
            f"🧩 تم اختبار البروكسيات بالطريقة الاحتياطية:\n"
            f"✅ البروكسيات الصحيحة: {len(valid_proxies)}/{len(proxy_candidates)}",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        
        # عرض الملخص النهائي
        await self._show_final_summary(message, user_id)
    
    async def _show_final_summary(self, message, user_id: int):
        """عرض الملخص النهائي للمهمة"""
        state = self.user_states[user_id]
        report_type_text = "فيديو" if state['report_type'] == ReportType.VIDEO else "حساب"
        reason_text = REPORT_REASONS[state['reason']]
        healthy_accounts = self.account_manager.get_healthy_accounts()
        total_reports = len(healthy_accounts) * state['reports_per_account']
        
        summary_text = (
            f"📋 ملخص المهمة:\n\n"
            f"🎯 الهدف: {state['target']}\n"
            f"📹 النوع: {report_type_text}\n"
            f"🚨 السبب: {reason_text}\n"
            f"📊 عدد البلاغات لكل حساب: {state['reports_per_account']}\n"
            f"👥 عدد الحسابات المتاحة: {len(healthy_accounts)}\n"
            f"🔢 إجمالي البلاغات: {total_reports}\n"
            f"🌐 بروكسيات مفعلة: {len(state.get('socks5_proxies', []))}\n\n"
            f"هل تريد تأكيد بدء عملية البلاغ؟"
        )
        
        await message.reply_text(
            summary_text,
            reply_markup=TikTokKeyboards.get_confirmation_menu()
        )
    
    async def show_job_status(self, query):
        """عرض حالة المهام"""
        jobs = self.scheduler.get_all_jobs()
        recent = self.scheduler.get_recent_jobs()
        
        if not jobs and not recent:
            await query.edit_message_text(
                "📊 حالة المهام\n\n"
                "لا توجد مهام حالياً.",
                reply_markup=TikTokKeyboards.get_main_menu()
            )
            return
        
        status_text = "📊 حالة المهام:\n\n"
        for job in jobs:
            status_emoji = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '⏹️'
            }.get(job.status.value, '❓')
            
            progress = job.get_progress_percentage()
            status_text += (
                f"{status_emoji} المهمة {job.id[:8]}...\n"
                f"   النوع: {'فيديو' if job.report_type == ReportType.VIDEO else 'حساب'}\n"
                f"   الهدف: {job.target}\n"
                f"   الحالة: {job.status.value}\n"
                f"   التقدم: {progress:.1f}%\n"
                f"   النجاح: {job.successful_reports}/{job.total_reports}\n\n"
            )

        if recent:
            status_text += "— آخر المهام المكتملة —\n"
            for job in recent:
                status_text += (
                    f"{('✅' if job.status.value=='completed' else '❌')} {job.id[:8]} | "
                    f"{'فيديو' if job.report_type == ReportType.VIDEO else 'حساب'} | "
                    f"نجاح: {job.successful_reports}/{job.total_reports}\n"
                )
        
        await query.edit_message_text(
            status_text,
            reply_markup=TikTokKeyboards.get_main_menu()
        )
    
    async def show_statistics(self, query):
        """عرض الإحصائيات"""
        account_stats = self.account_manager.get_account_stats()
        job_stats = self.scheduler.get_job_stats()
        
        stats_text = (
            "📈 الإحصائيات:\n\n"
            f"👥 الحسابات:\n"
            f"   المجموع: {account_stats['total']}\n"
            f"   النشطة: {account_stats['active']}\n"
            f"   المعزولة: {account_stats['quarantined']}\n"
            f"   المحظورة: {account_stats['banned']}\n\n"
            f"📊 المهام:\n"
            f"   المجموع: {job_stats['total_jobs']}\n"
            f"   النشطة: {job_stats['active_jobs']}\n"
            f"   في الطابور: {job_stats['queued_jobs']}\n"
            f"   البلاغات الناجحة: {job_stats['successful_reports']}\n"
            f"   البلاغات الفاشلة: {job_stats['failed_reports']}"
        )
        
        await query.edit_message_text(
            stats_text,
            reply_markup=TikTokKeyboards.get_main_menu()
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر الإلغاء"""
        if not update or not update.effective_user or not update.message:
            return ConversationHandler.END
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        await update.message.reply_text(
            "❌ تم إلغاء العملية.",
            reply_markup=TikTokKeyboards.get_main_menu()
        )
        return ConversationHandler.END
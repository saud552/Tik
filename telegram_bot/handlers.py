from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from core.account_manager import TikTokAccountManager
from core.report_scheduler import ReportScheduler
from core.tiktok_reporter import TikTokReporter
from models.job import ReportType
from telegram_bot.keyboards import TikTokKeyboards
from config.settings import ADMIN_USER_ID, REPORT_REASONS

# حالات المحادثة
(
    WAITING_FOR_USERNAME,
    WAITING_FOR_PASSWORD,
    WAITING_FOR_TARGET,
    WAITING_FOR_REASON,
    WAITING_FOR_REPORTS_COUNT,
    WAITING_FOR_CONFIRMATION,
    WAITING_FOR_PROXIES
) = range(7)

class TikTokHandlers:
    def __init__(self):
        self.account_manager = TikTokAccountManager()
        self.scheduler = ReportScheduler(self.account_manager)
        self.reporter = TikTokReporter()
        self.user_states = {}  # لتخزين حالة المستخدم
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
        if not update or not update.effective_user or not update.message:
            return
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("❌ عذراً، هذا البوت متاح للمدير فقط.")
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
            'reports_per_account': None
        }
        
        report_type_text = "فيديو" if report_type == ReportType.VIDEO else "حساب"
        await query.edit_message_text(
            f"📝 الإبلاغ عن {report_type_text}\n\n"
            f"أدخل رابط {report_type_text} أو اسم المستخدم:",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        
        return WAITING_FOR_TARGET
    
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
        
        if query.data.startswith("reason_"):
            # اختيار نوع بلاغ محدد
            reason_id = int(query.data.split("_")[1])
            self.user_states[user_id]['reason'] = reason_id
            
            reason_text = REPORT_REASONS[reason_id]
            await query.edit_message_text(
                f"✅ تم اختيار نوع البلاغ: {reason_text}\n\n"
                "الآن اختر عدد البلاغات المراد تنفيذها من كل حساب:",
                reply_markup=TikTokKeyboards.get_reports_per_account_menu()
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
        """معالجة اختيار عدد البلاغات"""
        query = update.callback_query
        if not query:
            return ConversationHandler.END
        await query.answer()
        
        if query.data.startswith("reports_"):
            reports_count = int(query.data.split("_")[1])
            user_id = query.from_user.id
            self.user_states[user_id]['reports_per_account'] = reports_count
            
            # طلب البروكسيات (SOCKS5) اختيارياً
            await query.edit_message_text(
                "🧩 هل تريد إضافة بروكسيات SOCKS5؟\n"
                "أرسل قائمة البروكسيات بهذا الشكل (سطر لكل بروكسي):\n"
                "ip:port\n\n"
                "أرسل كلمة تخطي لتجاوز هذه الخطوة.",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_PROXIES
        elif query.data == "back_to_reasons":
            await query.edit_message_text(
                "اختر نوع البلاغ:",
                reply_markup=TikTokKeyboards.get_report_reasons_menu(self.user_states[query.from_user.id]['report_type'].value)
            )
            return WAITING_FOR_REASON
    
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
                # إنشاء مهمة البلاغ
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
        
        if not jobs:
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
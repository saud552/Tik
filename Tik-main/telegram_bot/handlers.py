import asyncio
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
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
    WAITING_FOR_CONFIRMATION
) = range(6)

class TikTokHandlers:
    def __init__(self):
        self.account_manager = TikTokAccountManager()
        self.scheduler = ReportScheduler(self.account_manager)
        self.reporter = TikTokReporter()
        self.user_states = {}  # لتخزين حالة المستخدم
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البداية"""
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
        await query.answer()
        
        if query.data == "manage_accounts":
            await query.edit_message_text(
                "🔐 إدارة حسابات TikTok\n\n"
                "اختر العملية المطلوبة:",
                reply_markup=TikTokKeyboards.get_account_management_menu()
            )
        elif query.data == "report_video":
            await self.start_report_process(query, ReportType.VIDEO)
        elif query.data == "report_account":
            await self.start_report_process(query, ReportType.ACCOUNT)
        elif query.data == "job_status":
            await self.show_job_status(query)
        elif query.data == "statistics":
            await self.show_statistics(query)
        elif query.data == "main_menu":
            await self.start_command(update, context)
    
    async def start_report_process(self, query, report_type: ReportType):
        """بدء عملية البلاغ"""
        user_id = query.from_user.id
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
            reply_markup=TikTokKeyboards.get_report_reasons_menu()
        )
        
        return WAITING_FOR_REASON
    
    async def handle_reason_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار نوع البلاغ"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("reason_"):
            reason_id = int(query.data.split("_")[1])
            user_id = query.from_user.id
            self.user_states[user_id]['reason'] = reason_id
            
            reason_text = list(REPORT_REASONS.values())[reason_id - 1]
            await query.edit_message_text(
                f"✅ تم اختيار نوع البلاغ: {reason_text}\n\n"
                "الآن اختر عدد البلاغات المراد تنفيذها من كل حساب:",
                reply_markup=TikTokKeyboards.get_reports_per_account_menu()
            )
            
            return WAITING_FOR_REPORTS_COUNT
        elif query.data == "back_to_target":
            user_id = query.from_user.id
            del self.user_states[user_id]
            await query.edit_message_text(
                "📝 الإبلاغ عن فيديو\n\n"
                "أدخل رابط الفيديو:",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )
            return WAITING_FOR_TARGET
    
    async def handle_reports_count_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة اختيار عدد البلاغات"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("reports_"):
            reports_count = int(query.data.split("_")[1])
            user_id = query.from_user.id
            self.user_states[user_id]['reports_per_account'] = reports_count
            
            # عرض ملخص المهمة
            state = self.user_states[user_id]
            report_type_text = "فيديو" if state['report_type'] == ReportType.VIDEO else "حساب"
            reason_text = REPORT_REASONS[state['reason']]
            
            healthy_accounts = self.account_manager.get_healthy_accounts()
            total_reports = len(healthy_accounts) * reports_count
            
            summary_text = (
                f"📋 ملخص المهمة:\n\n"
                f"🎯 الهدف: {state['target']}\n"
                f"📹 النوع: {report_type_text}\n"
                f"🚨 السبب: {reason_text}\n"
                f"📊 عدد البلاغات لكل حساب: {reports_count}\n"
                f"👥 عدد الحسابات المتاحة: {len(healthy_accounts)}\n"
                f"🔢 إجمالي البلاغات: {total_reports}\n\n"
                f"هل تريد تأكيد بدء عملية البلاغ؟"
            )
            
            await query.edit_message_text(
                summary_text,
                reply_markup=TikTokKeyboards.get_confirmation_menu()
            )
            
            return WAITING_FOR_CONFIRMATION
        elif query.data == "back_to_reasons":
            await query.edit_message_text(
                "اختر نوع البلاغ:",
                reply_markup=TikTokKeyboards.get_report_reasons_menu()
            )
            return WAITING_FOR_REASON
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة تأكيد المهمة"""
        query = update.callback_query
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
                    reports_per_account=state['reports_per_account']
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
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        await update.message.reply_text(
            "❌ تم إلغاء العملية.",
            reply_markup=TikTokKeyboards.get_main_menu()
        )
        return ConversationHandler.END
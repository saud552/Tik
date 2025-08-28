import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config.settings import TELEGRAM_BOT_TOKEN
from telegram_bot.handlers import TikTokHandlers
from telegram_bot.keyboards import TikTokKeyboards

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

class TikTokBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.handlers = TikTokHandlers()
        self.setup_handlers()
    
    def setup_handlers(self):
        """إعداد جميع المعالجات"""
        
        # معالج أمر البداية
        start_handler = CommandHandler('start', self.handlers.start_command)
        self.application.add_handler(start_handler)
        # أوامر إدارية: تحديث/عرض المخطط
        self.application.add_handler(CommandHandler('refresh_schema', self.handlers.admin_refresh_schema))
        self.application.add_handler(CommandHandler('show_schema', self.handlers.admin_show_schema))
        
        # معالج إضافة الحساب
        add_account_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add_account, pattern='^add_account$')
            ],
            states={
                WAITING_FOR_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_username_input)
                ],
                WAITING_FOR_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_password_input)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.handlers.cancel_command)]
        )
        self.application.add_handler(add_account_handler)
        
        # معالج البلاغات
        report_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.handlers.start_report_process, pattern='^report_(video|account)$')
            ],
            states={
                WAITING_FOR_TARGET: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_target_input)
                ],
                WAITING_FOR_REASON: [
                    CallbackQueryHandler(self.handlers.handle_reason_selection)
                ],
                WAITING_FOR_REPORTS_COUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_reports_count_selection)
                ],
                WAITING_FOR_INTERVAL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_interval_input)
                ],
                WAITING_FOR_PROXIES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_proxies_input)
                ],
                WAITING_FOR_CONFIRMATION: [
                    CallbackQueryHandler(self.handlers.handle_confirmation)
                ]
            },
            fallbacks=[CommandHandler('cancel', self.handlers.cancel_command)]
        )
        self.application.add_handler(report_handler)
        
        # معالج القوائم الرئيسية (تقييد النمط لمنع اعتراض أزرار أخرى)
        main_menu_handler = CallbackQueryHandler(
            self.handlers.main_menu_callback,
            pattern='^(manage_accounts|report_video|report_account|job_status|statistics|main_menu)$'
        )
        self.application.add_handler(main_menu_handler)
        
        # معالج إدارة الحسابات
        self.application.add_handler(
            CallbackQueryHandler(self.handle_account_management, pattern='^(check_accounts|delete_account)$')
        )

        # تأكيد حذف حساب محدد
        self.application.add_handler(
            CallbackQueryHandler(self.handle_delete_account_confirm, pattern='^delete_')
        )
        
        # معالج التحكم بالمهام
        self.application.add_handler(
            CallbackQueryHandler(self.handle_job_control, pattern='^(stop_job_|retry_job_)')
        )
        
        # معالج الإلغاء العام
        cancel_handler = CommandHandler('cancel', self.handlers.cancel_command)
        self.application.add_handler(cancel_handler)
        
        # معالج الأخطاء
        self.application.add_error_handler(self.error_handler)
    
    async def start_add_account(self, update, context):
        """بدء عملية إضافة حساب"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "➕ إضافة حساب جديد\n\n"
            "أدخل اسم المستخدم:",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        
        return WAITING_FOR_USERNAME
    
    async def handle_username_input(self, update, context):
        """معالجة إدخال اسم المستخدم"""
        user_id = update.message.from_user.id
        username = update.message.text.strip()
        
        # حفظ اسم المستخدم في حالة المستخدم
        if user_id not in self.handlers.user_states:
            self.handlers.user_states[user_id] = {}
        
        self.handlers.user_states[user_id]['username'] = username
        
        await update.message.reply_text(
            f"✅ تم تحديد اسم المستخدم: {username}\n\n"
            "الآن أدخل كلمة المرور:",
            reply_markup=TikTokKeyboards.get_cancel_keyboard()
        )
        
        return WAITING_FOR_PASSWORD
    
    async def handle_password_input(self, update, context):
        """معالجة إدخال كلمة المرور"""
        user_id = update.message.from_user.id
        password = update.message.text.strip()
        
        if user_id not in self.handlers.user_states:
            await update.message.reply_text("❌ جلسة منتهية. يرجى البدء من جديد.")
            return ConversationHandler.END
        
        username = self.handlers.user_states[user_id]['username']
        
        try:
            # إضافة الحساب
            account_id = self.handlers.account_manager.add_account(username, password)
            
            await update.message.reply_text(
                f"✅ تم إضافة الحساب بنجاح!\n\n"
                f"👤 اسم المستخدم: {username}\n"
                f"🆔 معرف الحساب: {account_id[:8]}...\n\n"
                f"⏳ جاري محاولة تسجيل الدخول عبر الويب لاستخراج الكوكيز...",
                reply_markup=TikTokKeyboards.get_cancel_keyboard()
            )

            # محاولة استخراج كوكيز الويب تلقائياً
            try:
                from core.tiktok_reporter import TikTokReporter
                from models.account import TikTokAccount
                account = self.handlers.account_manager.get_account(account_id)
                reporter = TikTokReporter(self.handlers.account_manager)
                password_plain = self.handlers.account_manager.get_decrypted_password(account_id)
                ok = await reporter.web_login_and_store_cookies(account, password_plain)
                if ok:
                    await update.message.reply_text(
                        "✅ تم استخراج كوكيز جلسة الويب بنجاح!\nيمكنك الآن تنفيذ بلاغات الويب عند الحاجة.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ تعذر استخراج كوكيز الويب تلقائياً.\nسيتم استخدام مسار الموبايل افتراضياً. يمكنك لاحقاً استيراد الكوكيز يدوياً.",
                        reply_markup=TikTokKeyboards.get_main_menu()
                    )
            except Exception as e:
                await update.message.reply_text(
                    f"⚠️ تعذر إتمام تسجيل دخول الويب تلقائياً: {e}\nسيتم استخدام مسار الموبايل افتراضياً.",
                    reply_markup=TikTokKeyboards.get_main_menu()
                )
            
            # تنظيف حالة المستخدم
            del self.handlers.user_states[user_id]
            
        except ValueError as e:
            await update.message.reply_text(
                f"❌ {str(e)}",
                reply_markup=TikTokKeyboards.get_main_menu()
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ فشل في إضافة الحساب: {str(e)}",
                reply_markup=TikTokKeyboards.get_main_menu()
            )
        
        return ConversationHandler.END
    
    async def handle_account_management(self, update, context):
        """معالجة إدارة الحسابات"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "check_accounts":
            await self.show_accounts_status(query)
        elif query.data == "delete_account":
            await self.show_delete_account_menu(query)

    async def handle_delete_account_confirm(self, update, context):
        """حذف الحساب المختار من القائمة"""
        query = update.callback_query
        await query.answer()
        try:
            account_id = query.data.split('delete_')[1]
            success = self.handlers.account_manager.remove_account(account_id)
            if success:
                await query.edit_message_text(
                    "✅ تم حذف الحساب بنجاح.",
                    reply_markup=TikTokKeyboards.get_account_management_menu()
                )
            else:
                await query.edit_message_text(
                    "❌ لم يتم العثور على الحساب أو فشل الحذف.",
                    reply_markup=TikTokKeyboards.get_account_management_menu()
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ حدث خطأ أثناء الحذف: {e}",
                reply_markup=TikTokKeyboards.get_account_management_menu()
            )
    
    async def show_accounts_status(self, query):
        """عرض حالة الحسابات"""
        accounts = self.handlers.account_manager.get_all_accounts()
        
        if not accounts:
            await query.edit_message_text(
                "🔍 فحص الحسابات\n\n"
                "لا توجد حسابات مسجلة.",
                reply_markup=TikTokKeyboards.get_account_management_menu()
            )
            return
        
        status_text = "🔍 حالة الحسابات:\n\n"
        for account in accounts:
            status_emoji = {
                'active': '🟢',
                'quarantined': '🟡',
                'banned': '🔴',
                'error': '❌'
            }.get(account.status, '❓')
            
            status_text += (
                f"{status_emoji} {account.username}\n"
                f"   الحالة: {account.status}\n"
                f"   النجاح: {account.success_count}\n"
                f"   الفشل: {account.fail_count}\n"
                f"   آخر استخدام: {account.last_used.strftime('%Y-%m-%d %H:%M') if account.last_used else 'لم يستخدم'}\n\n"
            )
        
        await query.edit_message_text(
            status_text,
            reply_markup=TikTokKeyboards.get_account_management_menu()
        )
    
    async def show_delete_account_menu(self, query):
        """عرض قائمة حذف الحسابات"""
        accounts = self.handlers.account_manager.get_all_accounts()
        
        if not accounts:
            await query.edit_message_text(
                "❌ حذف حساب\n\n"
                "لا توجد حسابات مسجلة.",
                reply_markup=TikTokKeyboards.get_account_management_menu()
            )
            return
        
        await query.edit_message_text(
            "❌ حذف حساب\n\n"
            "اختر الحساب المراد حذفه:",
            reply_markup=TikTokKeyboards.get_account_list_keyboard(accounts, "delete")
        )
    
    async def handle_job_control(self, update, context):
        """معالجة التحكم بالمهام"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("stop_job_"):
            job_id = query.data.split("stop_job_")[1]
            success = await self.handlers.scheduler.stop_job(job_id)
            
            if success:
                await query.edit_message_text(
                    f"⏹️ تم إيقاف المهمة {job_id[:8]}... بنجاح.",
                    reply_markup=TikTokKeyboards.get_main_menu()
                )
            else:
                await query.edit_message_text(
                    f"❌ فشل في إيقاف المهمة {job_id[:8]}...",
                    reply_markup=TikTokKeyboards.get_main_menu()
                )
        
        elif query.data.startswith("retry_job_"):
            job_id = query.data.split("retry_job_")[1]
            success = await self.handlers.scheduler.retry_failed_reports(job_id)
            
            if success:
                await query.edit_message_text(
                    f"🔄 تم إعادة تشغيل المهمة {job_id[:8]}... بنجاح.",
                    reply_markup=TikTokKeyboards.get_main_menu()
                )
            else:
                await query.edit_message_text(
                    f"❌ فشل في إعادة تشغيل المهمة {job_id[:8]}...",
                    reply_markup=TikTokKeyboards.get_main_menu()
                )
    
    async def error_handler(self, update, context):
        """معالج الأخطاء"""
        logger.error(f"حدث خطأ: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.",
                reply_markup=TikTokKeyboards.get_main_menu()
            )
    
    def run(self):
        """تشغيل البوت (حاجب)"""
        logger.info("بدء تشغيل بوت بلاغات TikTok...")
        self.application.run_polling()

# تشغيل البوت
if __name__ == "__main__":
    bot = TikTokBot()
    asyncio.run(bot.run())
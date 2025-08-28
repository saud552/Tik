from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config.settings import REPORT_REASONS

class TikTokKeyboards:
    @staticmethod
    def get_main_menu():
        """القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("🔐 التحكم بحسابات TikTok", callback_data="manage_accounts")],
            [InlineKeyboardButton("📹 الإبلاغ عن فيديو", callback_data="report_video")],
            [InlineKeyboardButton("👤 الإبلاغ عن حساب", callback_data="report_account")],
            [InlineKeyboardButton("📊 حالة المهام", callback_data="job_status")],
            [InlineKeyboardButton("📈 إحصائيات", callback_data="statistics")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_account_management_menu():
        """قائمة إدارة الحسابات"""
        keyboard = [
            [InlineKeyboardButton("➕ إضافة حساب جديد", callback_data="add_account")],
            [InlineKeyboardButton("🔍 فحص الحسابات", callback_data="check_accounts")],
            [InlineKeyboardButton("❌ حذف حساب", callback_data="delete_account")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_report_reasons_menu():
        """قائمة أنواع البلاغات"""
        keyboard = []
        for reason_id, reason_text in REPORT_REASONS.items():
            keyboard.append([InlineKeyboardButton(reason_text, callback_data=f"reason_{reason_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_target")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_reports_per_account_menu():
        """قائمة عدد البلاغات لكل حساب"""
        keyboard = [
            [InlineKeyboardButton("1", callback_data="reports_1")],
            [InlineKeyboardButton("2", callback_data="reports_2")],
            [InlineKeyboardButton("3", callback_data="reports_3")],
            [InlineKeyboardButton("4", callback_data="reports_4")],
            [InlineKeyboardButton("5", callback_data="reports_5")],
            [InlineKeyboardButton("🔙 العودة", callback_data="back_to_reasons")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation_menu():
        """قائمة التأكيد"""
        keyboard = [
            [InlineKeyboardButton("✅ تأكيد بدء البلاغ", callback_data="confirm_report")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_report")],
            [InlineKeyboardButton("🔙 العودة", callback_data="back_to_reports_count")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_job_control_menu(job_id: str):
        """قائمة التحكم بالمهمة"""
        keyboard = [
            [InlineKeyboardButton("⏹️ إيقاف المهمة", callback_data=f"stop_job_{job_id}")],
            [InlineKeyboardButton("🔄 إعادة المحاولة", callback_data=f"retry_job_{job_id}")],
            [InlineKeyboardButton("🔙 العودة", callback_data="job_status")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_cancel_keyboard():
        """زر الإلغاء"""
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_back_keyboard():
        """زر العودة"""
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="back")]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_yes_no_keyboard():
        """قائمة نعم/لا"""
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم", callback_data="yes"),
                InlineKeyboardButton("❌ لا", callback_data="no")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_account_list_keyboard(accounts, action: str):
        """قائمة الحسابات للاختيار"""
        keyboard = []
        for account in accounts:
            status_emoji = "🟢" if account.status == "active" else "🔴"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {account.username}", 
                    callback_data=f"{action}_{account.id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="manage_accounts")])
        return InlineKeyboardMarkup(keyboard)
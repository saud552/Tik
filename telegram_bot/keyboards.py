from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.settings import REPORT_REASONS, REPORT_CATEGORIES

class TikTokKeyboards:
    @staticmethod
    def _chunk_buttons(buttons, per_row: int = 2):
        """تقسيم الأزرار لصفوف متساوية"""
        chunked = []
        row = []
        for btn in buttons:
            row.append(btn)
            if len(row) == per_row:
                chunked.append(row)
                row = []
        if row:
            chunked.append(row)
        return chunked
    @staticmethod
    def get_main_menu():
        """القائمة الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("🔐 التحكم بحسابات TikTok", callback_data="manage_accounts")],
            [InlineKeyboardButton("📹 الإبلاغ عن فيديو", callback_data="report_video")],
            [InlineKeyboardButton("👤 الإبلاغ عن حساب", callback_data="report_account")],
            [InlineKeyboardButton("🧭 تسجيل دخول الويب للحسابات", callback_data="web_login_all")],
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
    def get_report_reasons_menu(report_type="video"):
        """قائمة أنواع البلاغات مع فئات منظمة"""
        keyboard = []
        rows: list[list[InlineKeyboardButton]] = []
        
        # اختيار قواميس الفئات
        categories = REPORT_CATEGORIES.get('video' if report_type == "video" else 'account', {})
        # ترجمات الفئات
        category_labels_video = {
            'sexual': '🔞 محتوى جنسي',
            'violent': '⚔️ عنف وإيذاء',
            'harassment': '🚫 تحرش وإساءة',
            'misinformation': '❌ معلومات خاطئة',
            'impersonation': '👤 انتحال شخصية',
            'copyright': '📜 حقوق الملكية',
            'discrimination': '🚷 تمييز وعنصرية',
            'commercial': '💰 محتوى تجاري',
            'other': '📝 أخرى'
        }
        category_labels_account = {
            'spam': '📧 رسائل مزعجة',
            'fake': '🎭 حسابات مزيفة',
            'harmful': '🚫 محتوى ضار',
            'inappropriate': '⚠️ محتوى غير مناسب',
            'other': '📝 أخرى'
        }

        btns = []
        for category_name, reason_ids in categories.items():
            if not reason_ids:
                continue
            label = (category_labels_video if report_type == "video" else category_labels_account).get(
                category_name, category_name.title()
            )
            btns.append(InlineKeyboardButton(label, callback_data=f"category_{category_name}"))

        rows.extend(TikTokKeyboards._chunk_buttons(btns, per_row=2))
        # زر عرض الكل
        rows.append([InlineKeyboardButton("📋 عرض جميع الأنواع", callback_data="show_all_reasons")])
        
        rows.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_target")])
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def get_dynamic_categories_menu(categories: list[dict]):
        """قائمة فئات البلاغات الديناميكية المستخرجة من الويب"""
        rows: list[list[InlineKeyboardButton]] = []
        btns = []
        for cat in categories:
            title = cat.get('title', 'Category')
            key = cat.get('key', title)
            btns.append(InlineKeyboardButton(title, callback_data=f"dyncat_{key}"))
        rows.extend(TikTokKeyboards._chunk_buttons(btns, per_row=2))
        rows.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_target")])
        return InlineKeyboardMarkup(rows)

    @staticmethod
    def get_dynamic_items_menu(categories: list[dict], category_key: str):
        """قائمة العناصر (الأسباب) لفئة ديناميكية محددة"""
        rows: list[list[InlineKeyboardButton]] = []
        items = []
        for cat in categories:
            if cat.get('key') == category_key:
                items = cat.get('items', [])
                break
        btns = []
        for it in items:
            title = it.get('title', 'Reason')
            rid = it.get('id', title)
            label = title if len(title) <= 34 else (title[:31] + "...")
            btns.append(InlineKeyboardButton(label, callback_data=f"dynitem_{rid}"))
        if btns:
            rows.extend(TikTokKeyboards._chunk_buttons(btns, per_row=2))
        rows.append([InlineKeyboardButton("🔙 العودة للفئات", callback_data="back_to_categories")])
        return InlineKeyboardMarkup(rows)
    
    @staticmethod
    def get_category_reasons_menu(category: str, report_type: str = "video"):
        """قائمة أنواع البلاغات لفئة محددة"""
        rows: list[list[InlineKeyboardButton]] = []
        categories = REPORT_CATEGORIES.get(report_type, {})
        reason_ids = categories.get(category, [])
        # تصفية بحيث تكون معرفة فعلياً
        valid_reasons = sorted([r for r in reason_ids if r in REPORT_REASONS])

        btns = []
        for rid in valid_reasons:
            title = REPORT_REASONS[rid]
            label = f"{title} ({rid})"
            if len(label) > 34:
                label = label[:31] + "..."
            btns.append(InlineKeyboardButton(label, callback_data=f"reason_{rid}"))

        rows.extend(TikTokKeyboards._chunk_buttons(btns, per_row=2))
        rows.append([InlineKeyboardButton("🔙 العودة للفئات", callback_data="back_to_categories")])
        return InlineKeyboardMarkup(rows)
    
    @staticmethod
    def get_all_reasons_menu(report_type: str = "video"):
        """قائمة جميع أنواع البلاغات"""
        rows: list[list[InlineKeyboardButton]] = []
        categories = REPORT_CATEGORIES.get(report_type, {})
        # تجميع جميع الأسباب الفريدة
        all_ids = set()
        for _, reason_ids in categories.items():
            all_ids.update([r for r in reason_ids if r in REPORT_REASONS])
        btns = []
        for rid in sorted(all_ids):
            title = REPORT_REASONS[rid]
            label = f"{title} ({rid})"
            if len(label) > 34:
                label = label[:31] + "..."
            btns.append(InlineKeyboardButton(label, callback_data=f"reason_{rid}"))
        rows.extend(TikTokKeyboards._chunk_buttons(btns, per_row=2))
        rows.append([InlineKeyboardButton("🔙 العودة للفئات", callback_data="back_to_categories")])
        return InlineKeyboardMarkup(rows)
    
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
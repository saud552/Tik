#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف تشغيل مبسط لبوت بلاغات TikTok
"""

import asyncio
import sys
from pathlib import Path

# إضافة المجلدات إلى مسار Python
sys.path.append(str(Path(__file__).parent))

try:
    from telegram_bot.bot import TikTokBot
    from config.settings import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
    
    print("🎯 بوت بلاغات TikTok - النسخة المحسنة")
    print("=" * 50)
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ يرجى تعيين TELEGRAM_BOT_TOKEN في ملف .env")
        sys.exit(1)
    
    if not ADMIN_USER_ID:
        print("❌ يرجى تعيين ADMIN_USER_ID في ملف .env")
        sys.exit(1)
    
    print("✅ تم تحميل الإعدادات بنجاح")
    print("🚀 بدء تشغيل البوت...")
    
    # تشغيل البوت
    bot = TikTokBot()
    asyncio.run(bot.run())
    
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    print("💡 تأكد من تثبيت المتطلبات: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ خطأ غير متوقع: {e}")
    sys.exit(1)
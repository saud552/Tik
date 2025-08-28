#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت بلاغات TikTok - النسخة المحسنة
نظام متكامل لإدارة حسابات TikTok وتنفيذ البلاغات تلقائياً
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# إضافة المجلدات إلى مسار Python
sys.path.append(str(Path(__file__).parent))

from telegram_bot.bot import TikTokBot
from config.settings import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tiktok_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """الدالة الرئيسية"""
    try:
        # التحقق من وجود التوكن
        if not TELEGRAM_BOT_TOKEN:
            logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN في ملف .env")
            print("❌ يرجى إنشاء ملف .env وإضافة TELEGRAM_BOT_TOKEN")
            return
        
        # التحقق من معرف المدير
        if not ADMIN_USER_ID:
            logger.error("❌ لم يتم تعيين ADMIN_USER_ID في ملف .env")
            print("❌ يرجى إنشاء ملف .env وإضافة ADMIN_USER_ID")
            return
        
        logger.info("🚀 بدء تشغيل بوت بلاغات TikTok...")
        print("🚀 بدء تشغيل بوت بلاغات TikTok...")
        
        # إنشاء وتشغيل البوت
        bot = TikTokBot()
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        print("⏹️ تم إيقاف البوت")
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        print(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    # إنشاء المجلدات المطلوبة
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    print("=" * 50)
    print("🎯 بوت بلاغات TikTok - النسخة المحسنة")
    print("=" * 50)
    print("📱 نظام متكامل لإدارة حسابات TikTok")
    print("🚨 تنفيذ البلاغات تلقائياً وبكفاءة عالية")
    print("🔒 حماية متقدمة ضد الكشف")
    print("=" * 50)
    
    # تشغيل النظام
    asyncio.run(main())
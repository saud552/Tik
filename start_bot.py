#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف تشغيل بوت بلاغات TikTok
"""

import os
import sys
from pathlib import Path

def check_environment():
    """فحص البيئة والتأكد من وجود الملفات المطلوبة"""
    print("🔍 فحص البيئة...")
    
    # فحص وجود ملف .env
    if not os.path.exists('.env'):
        print("❌ ملف .env غير موجود!")
        print("💡 قم بنسخ .env.example إلى .env وتعديله")
        return False
    
    # فحص وجود المجلدات المطلوبة
    required_dirs = ['data', 'logs']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ تم إنشاء مجلد {dir_name}")
    
    return True

def check_dependencies():
    """فحص المكتبات المطلوبة"""
    print("🔍 فحص المكتبات...")
    
    required_modules = [
        'telegram',
        'requests',
        'dotenv',
        'cryptography'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")
    
    if missing_modules:
        print(f"\n❌ المكتبات التالية مفقودة: {', '.join(missing_modules)}")
        print("💡 قم بتثبيت المكتبات باستخدام:")
        print("pip3 install --break-system-packages python-telegram-bot==20.7 requests==2.31.0 python-dotenv==1.0.0 cryptography==41.0.7")
        return False
    
    return True

def run_tests():
    """تشغيل الاختبارات الأساسية"""
    print("🧪 تشغيل الاختبارات الأساسية...")
    
    try:
        # تشغيل الاختبار الأساسي
        result = os.system('python3 basic_test.py')
        if result == 0:
            print("✅ جميع الاختبارات الأساسية نجحت!")
            return True
        else:
            print("❌ بعض الاختبارات الأساسية فشلت!")
            return False
    except Exception as e:
        print(f"❌ خطأ في تشغيل الاختبارات: {e}")
        return False

def start_bot():
    """تشغيل البوت"""
    print("🚀 تشغيل البوت...")
    
    try:
        # إضافة المجلد الحالي إلى مسار Python
        sys.path.append(str(Path(__file__).parent))
        
        # استيراد وتشغيل البوت
        from telegram_bot.bot import TikTokBot
        from config.settings import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
        
        # فحص الإعدادات
        if TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
            print("❌ يرجى تعديل TELEGRAM_BOT_TOKEN في ملف .env")
            return False
        
        if ADMIN_USER_ID == 123456789:
            print("❌ يرجى تعديل ADMIN_USER_ID في ملف .env")
            return False
        
        print("✅ الإعدادات صحيحة")
        print("🤖 بدء تشغيل البوت...")
        
        # تشغيل البوت
        bot = TikTokBot()
        bot.run()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🤖 بوت بلاغات TikTok - ملف التشغيل")
    print("=" * 50)
    
    # فحص البيئة
    if not check_environment():
        return False
    
    print()
    
    # فحص المكتبات
    if not check_dependencies():
        return False
    
    print()
    
    # تشغيل الاختبارات
    if not run_tests():
        print("\n💡 يرجى إصلاح الأخطاء قبل تشغيل البوت")
        return False
    
    print()
    
    # تشغيل البوت
    return start_bot()

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ فشل في تشغيل البوت")
        print("💡 راجع الأخطاء أعلاه وحاول مرة أخرى")
        sys.exit(1)
    else:
        print("\n🎉 تم تشغيل البوت بنجاح!")
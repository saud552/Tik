#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار أساسي لمكونات بوت بلاغات TikTok
"""

import sys
import os
from pathlib import Path

# إضافة المجلدات إلى مسار Python
sys.path.append(str(Path(__file__).parent))

def test_file_structure():
    """اختبار هيكل الملفات"""
    print("🧪 اختبار هيكل الملفات...")
    
    required_files = [
        'core/account_manager.py',
        'core/report_scheduler.py',
        'core/tiktok_reporter.py',
        'models/account.py',
        'models/job.py',
        'utils/encryption.py',
        'config/settings.py',
        'telegram_bot/keyboards.py',
        'telegram_bot/handlers.py',
        'telegram_bot/bot.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ جميع الملفات المطلوبة موجودة")
        return True
    else:
        print("❌ الملفات التالية مفقودة:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

def test_python_syntax():
    """اختبار صحة بناء Python"""
    print("\n🧪 اختبار صحة بناء Python...")
    
    python_files = [
        'models/account.py',
        'models/job.py',
        'utils/encryption.py',
        'config/settings.py',
        'telegram_bot/keyboards.py'
    ]
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                compile(content, file_path, 'exec')
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
        except Exception as e:
            syntax_errors.append(f"{file_path}: {e}")
    
    if not syntax_errors:
        print("✅ جميع ملفات Python صحيحة بناءً")
        return True
    else:
        print("❌ أخطاء في بناء Python:")
        for error in syntax_errors:
            print(f"   - {error}")
        return False

def test_basic_models():
    """اختبار النماذج الأساسية"""
    print("\n🧪 اختبار النماذج الأساسية...")
    
    try:
        # اختبار إنشاء حساب بسيط
        from models.account import TikTokAccount
        
        account = TikTokAccount(
            id="test_id",
            username="test_user",
            encrypted_password="encrypted_pass",
            encrypted_cookies="encrypted_cookies"
        )
        
        if account.username == "test_user":
            print("✅ تم إنشاء نموذج الحساب بنجاح")
        else:
            print("❌ فشل في إنشاء نموذج الحساب")
            return False
        
        # اختبار إنشاء مهمة بسيطة
        from models.job import ReportJob, ReportType
        
        job = ReportJob(
            report_type=ReportType.VIDEO,
            target="https://tiktok.com/@test/video/123",
            reason=1,
            reports_per_account=2
        )
        
        if job.target == "https://tiktok.com/@test/video/123":
            print("✅ تم إنشاء نموذج المهمة بنجاح")
        else:
            print("❌ فشل في إنشاء نموذج المهمة")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ فشل في اختبار النماذج: {e}")
        return False

def test_config_structure():
    """اختبار هيكل الإعدادات"""
    print("\n🧪 اختبار هيكل الإعدادات...")
    
    try:
        # محاولة قراءة ملف الإعدادات
        with open('config/settings.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # فحص وجود المتغيرات المطلوبة
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'ADMIN_USER_ID',
            'TIKTOK_BASE_URL',
            'REPORT_REASONS',
            'HUMAN_DELAYS'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if not missing_vars:
            print("✅ جميع المتغيرات المطلوبة موجودة في الإعدادات")
            return True
        else:
            print("❌ المتغيرات التالية مفقودة:")
            for var in missing_vars:
                print(f"   - {var}")
            return False
        
    except Exception as e:
        print(f"❌ فشل في اختبار الإعدادات: {e}")
        return False

def test_telegram_structure():
    """اختبار هيكل بوت تيليجرام"""
    print("\n🧪 اختبار هيكل بوت تيليجرام...")
    
    try:
        # فحص وجود الملفات المطلوبة
        telegram_files = [
            'telegram_bot/keyboards.py',
            'telegram_bot/handlers.py',
            'telegram_bot/bot.py'
        ]
        
        for file_path in telegram_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # فحص وجود الفئات المطلوبة
            if 'TikTokKeyboards' in content:
                print(f"✅ {file_path}: فئة TikTokKeyboards موجودة")
            else:
                print(f"❌ {file_path}: فئة TikTokKeyboards مفقودة")
                return False
        
        print("✅ جميع فئات بوت تيليجرام موجودة")
        return True
        
    except Exception as e:
        print(f"❌ فشل في اختبار بوت تيليجرام: {e}")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار أساسي لمكونات بوت بلاغات TikTok")
    print("=" * 60)
    
    tests = [
        ("هيكل الملفات", test_file_structure),
        ("صحة بناء Python", test_python_syntax),
        ("النماذج الأساسية", test_basic_models),
        ("هيكل الإعدادات", test_config_structure),
        ("هيكل بوت تيليجرام", test_telegram_structure)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 اختبار: {test_name}")
        if test_func():
            passed_tests += 1
            print(f"✅ نجح اختبار: {test_name}")
        else:
            print(f"❌ فشل اختبار: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"📊 نتائج الاختبار: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 جميع الاختبارات الأساسية نجحت!")
        print("✅ البوت جاهز للتشغيل (بعد تثبيت المكتبات)")
        return True
    else:
        print("❌ بعض الاختبارات الأساسية فشلت")
        print("💡 يرجى مراجعة الأخطاء وإصلاحها")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
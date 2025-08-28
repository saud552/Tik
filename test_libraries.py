#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار المكتبات المثبتة
"""

def test_telegram_bot():
    """اختبار مكتبة python-telegram-bot"""
    print("🧪 اختبار مكتبة python-telegram-bot...")
    
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # اختبار إنشاء أزرار
        button = InlineKeyboardButton("اختبار", callback_data="test")
        _ = InlineKeyboardMarkup([[button]])
        
        print("✅ تم استيراد python-telegram-bot بنجاح")
        print("✅ تم إنشاء أزرار تفاعلية بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ فشل في اختبار python-telegram-bot: {e}")
        return False

def test_requests():
    """اختبار مكتبة requests"""
    print("\n🧪 اختبار مكتبة requests...")
    
    try:
        import requests
        
        # اختبار طلب بسيط
        response = requests.get("https://httpbin.org/get", timeout=5)
        
        if response.status_code == 200:
            print("✅ تم استيراد requests بنجاح")
            print("✅ تم إرسال طلب HTTP بنجاح")
            return True
        else:
            print(f"⚠️ الطلب نجح لكن الكود: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"❌ فشل في اختبار requests: {e}")
        return False

def test_dotenv():
    """اختبار مكتبة python-dotenv"""
    print("\n🧪 اختبار مكتبة python-dotenv...")
    
    try:
        from dotenv import load_dotenv
        import os
        
        # اختبار تحميل متغيرات البيئة
        load_dotenv()
        _ = os.getenv('TEST_VAR', 'default_value')
        
        print("✅ تم استيراد python-dotenv بنجاح")
        print("✅ تم تحميل متغيرات البيئة بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ فشل في اختبار python-dotenv: {e}")
        return False

def test_cryptography():
    """اختبار مكتبة cryptography"""
    print("\n🧪 اختبار مكتبة cryptography...")
    
    try:
        from cryptography.fernet import Fernet
        
        # اختبار إنشاء مفتاح
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        
        # اختبار التشفير
        test_data = "بيانات_اختبار_123"
        encrypted = cipher_suite.encrypt(test_data.encode())
        decrypted = cipher_suite.decrypt(encrypted).decode()
        
        if test_data == decrypted:
            print("✅ تم استيراد cryptography بنجاح")
            print("✅ تم تشفير وفك تشفير البيانات بنجاح")
            return True
        else:
            print("❌ فشل في اختبار التشفير")
            return False
            
    except Exception as e:
        print(f"❌ فشل في اختبار cryptography: {e}")
        return False

def test_tiktok_components():
    """اختبار مكونات TikTok"""
    print("\n🧪 اختبار مكونات TikTok...")
    
    try:
        # اختبار النماذج
        from models.account import TikTokAccount
        from models.job import ReportJob, ReportType
        
        _account = TikTokAccount(
            id="test_id",
            username="test_user",
            encrypted_password="encrypted_pass",
            encrypted_cookies="encrypted_cookies"
        )
        
        _job = ReportJob(
            report_type=ReportType.VIDEO,
            target="https://tiktok.com/@test/video/123",
            reason=1,
            reports_per_account=2
        )
        
        print("✅ تم استيراد نماذج TikTok بنجاح")
        print("✅ تم إنشاء حساب ومهمة بنجاح")
        return True
        
    except Exception as e:
        print(f"❌ فشل في اختبار مكونات TikTok: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🧪 اختبار المكتبات المثبتة")
    print("=" * 50)
    
    tests = [
        ("python-telegram-bot", test_telegram_bot),
        ("requests", test_requests),
        ("python-dotenv", test_dotenv),
        ("cryptography", test_cryptography),
        ("مكونات TikTok", test_tiktok_components)
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
    
    print("\n" + "=" * 50)
    print(f"📊 نتائج اختبار المكتبات: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 جميع المكتبات تعمل بشكل مثالي!")
        print("✅ البوت جاهز للاستخدام الكامل")
        print("\n🚀 يمكنك الآن:")
        print("   1. إنشاء ملف .env مع الإعدادات")
        print("   2. تشغيل البوت: python3 run.py")
        print("   3. البدء في استخدام جميع الميزات")
        return True
    else:
        print("❌ بعض المكتبات لا تعمل بشكل صحيح")
        print("💡 يرجى مراجعة الأخطاء وإصلاحها")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
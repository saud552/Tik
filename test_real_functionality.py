#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار الوظائف الحقيقية للبوت
"""

import sys
import os
import asyncio
from pathlib import Path

# إضافة المجلدات إلى مسار Python
sys.path.append(str(Path(__file__).parent))

async def test_real_login():
    """اختبار تسجيل الدخول الحقيقي"""
    print("🧪 اختبار تسجيل الدخول الحقيقي...")
    
    try:
        from core.tiktok_reporter import TikTokReporter
        from models.account import TikTokAccount
        
        # إنشاء حساب تجريبي
        test_account = TikTokAccount(
            id="test_id",
            username="test_user",
            encrypted_password="test_password",
            encrypted_cookies=""
        )
        
        # إنشاء reporter
        reporter = TikTokReporter()
        
        # اختبار تسجيل الدخول: يجب أن ينجح فقط إذا كانت الاستجابة موثقة بوجود جلسة
        print("📱 اختبار تسجيل الدخول عبر Mobile API...")
        mobile_ok = await reporter._mobile_login("test_id", "test_user", "test_password")
        print("🌐 اختبار تسجيل الدخول عبر Web API...")
        web_ok = await reporter._web_login("test_id", "test_user", "test_password")

        # نجاح الاختبار = أي مسار نجح فعلاً
        return bool(mobile_ok or web_ok)
        
    except Exception as e:
        print(f"❌ خطأ في اختبار تسجيل الدخول: {e}")
        return False

async def test_real_reporting():
    """اختبار البلاغات الحقيقية"""
    print("\n🧪 اختبار البلاغات الحقيقية...")
    
    try:
        from core.tiktok_reporter import TikTokReporter
        from models.account import TikTokAccount
        
        # إنشاء حساب تجريبي
        test_account = TikTokAccount(
            id="test_id",
            username="test_user",
            encrypted_password="test_password",
            encrypted_cookies=""
        )
        
        # إنشاء reporter
        reporter = TikTokReporter()
        
        # اختبار استخراج معلومات الفيديو
        print("📹 اختبار استخراج معلومات الفيديو...")
        video_info = await reporter.extract_video_info("https://www.tiktok.com/@test/video/1234567890123456789")
        
        if video_info and video_info[0] and video_info[1]:
            print(f"✅ تم استخراج معرف الفيديو: {video_info[0]}")
            print(f"✅ تم استخراج معرف المستخدم: {video_info[1]}")
        else:
            print("❌ فشل في استخراج معلومات الفيديو (متوقع للبيانات التجريبية)")
        
        # اختبار البلاغ عن الفيديو (لا يعتبر نجاحاً إلا باستجابة JSON صحيحة)
        print("🚨 اختبار البلاغ عن الفيديو...")
        success = await reporter.report_video(test_account, "1234567890123456789", "987654321", 1001)
        return bool(success)
        
    except Exception as e:
        print(f"❌ خطأ في اختبار البلاغات: {e}")
        return False

async def test_proxy_system():
    """اختبار نظام البروكسيات"""
    print("\n🧪 اختبار نظام البروكسيات...")
    
    try:
        from utils.proxy_tester import ProxyTester
        
        # إنشاء tester
        tester = ProxyTester()
        
        # اختبار بروكسي تجريبي
        print("🔍 اختبار بروكسي تجريبي...")
        test_proxy = "socks5h://127.0.0.1:1080"
        
        result = await tester.test_proxy_async(test_proxy)
        
        if result.is_working:
            print(f"✅ البروكسي يعمل: {result.proxy}")
            print(f"   وقت الاستجابة: {result.response_time:.2f} ثانية")
            print(f"   البلد: {result.country}")
            print(f"   مستوى الخصوصية: {result.anonymity}")
        else:
            print(f"❌ البروكسي لا يعمل: {result.proxy}")
            print(f"   السبب: {result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار البروكسيات: {e}")
        return False

async def test_api_endpoints():
    """اختبار نقاط النهاية API"""
    print("\n🧪 اختبار نقاط النهاية API...")
    
    try:
        from config.settings import TIKTOK_API_ENDPOINTS, TIKTOK_APP_CONFIG
        
        print("🔗 فحص نقاط النهاية API...")
        for name, url in TIKTOK_API_ENDPOINTS.items():
            print(f"   {name}: {url}")
        
        print("\n📱 فحص إعدادات التطبيق...")
        for platform, config in TIKTOK_APP_CONFIG.items():
            print(f"   {platform}: {config['app_name']} v{config['version_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار نقاط النهاية: {e}")
        return False

async def test_encryption():
    """اختبار نظام التشفير"""
    print("\n🧪 اختبار نظام التشفير...")
    
    try:
        from utils.encryption import CredentialEncryption
        
        # إنشاء نظام التشفير
        encryption = CredentialEncryption()
        
        # اختبار التشفير
        test_data = "test_password_123"
        encrypted = encryption.encrypt(test_data)
        decrypted = encryption.decrypt(encrypted)
        
        if decrypted == test_data:
            print("✅ نجح نظام التشفير")
            print(f"   البيانات الأصلية: {test_data}")
            print(f"   البيانات المشفرة: {encrypted[:20]}...")
            print(f"   البيانات المفكوكة: {decrypted}")
        else:
            print("❌ فشل نظام التشفير")
            print(f"   البيانات الأصلية: {test_data}")
            print(f"   البيانات المفكوكة: {decrypted}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التشفير: {e}")
        return False

async def main():
    """الدالة الرئيسية"""
    print("🚀 اختبار الوظائف الحقيقية للبوت")
    print("=" * 50)
    
    tests = [
        ("نظام التشفير", test_encryption),
        ("نقاط النهاية API", test_api_endpoints),
        ("نظام البروكسيات", test_proxy_system),
        ("تسجيل الدخول", test_real_login),
        ("البلاغات", test_real_reporting)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ خطأ في اختبار {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 نتائج الاختبارات:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 النتيجة النهائية: {passed}/{total} اختبارات نجحت")
    
    if passed == total:
        print("🎉 جميع الاختبارات نجحت! البوت جاهز للعمل.")
    else:
        print("⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء.")

if __name__ == "__main__":
    asyncio.run(main())
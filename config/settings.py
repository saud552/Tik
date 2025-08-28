import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات TikTok - محدثة وموثقة
TIKTOK_BASE_URL = "https://www.tiktok.com"
TIKTOK_MOBILE_API = "https://api-h2.tiktokv.com"
TIKTOK_WEB_API = "https://www.tiktok.com/api"
TIKTOK_PASSPORT_API = "https://www.tiktok.com/passport"

# إعدادات API محدثة وموثقة
TIKTOK_API_ENDPOINTS = {
    'login': 'https://www.tiktok.com/passport/web/login/',
    'login_mobile': 'https://api-h2.tiktokv.com/passport/mobile/login/',
    'report_video': 'https://api-h2.tiktokv.com/aweme/v2/aweme/feedback/',
    'report_user': 'https://api-h2.tiktokv.com/aweme/v2/user/feedback/',
    'report_web': 'https://www.tiktok.com/api/report/',
    'video_info': 'https://api-h2.tiktokv.com/aweme/v1/aweme/detail/',
    'user_info': 'https://api-h2.tiktokv.com/user/detail/',
    'search': 'https://api-h2.tiktokv.com/aweme/v1/general/search/'
}

# إعدادات التطبيق المحدثة والموثقة
TIKTOK_APP_CONFIG = {
    'web': {
        'aid': '1988',
        'app_name': 'tiktok_web',
        'version_code': '220100',
        'version_name': '22.1.0',
        'device_platform': 'webapp',
        'channel': 'tiktok_web'
    },
    'mobile_android': {
        'aid': '1233',
        'app_name': 'tiktok',
        'version_code': '370805',
        'version_name': '37.8.5',
        'device_platform': 'android',
        'channel': 'googleplay',
        'os': 'android',
        'cpu_abi': 'arm64-v8a'
    },
    'mobile_ios': {
        'aid': '1233',
        'app_name': 'tiktok',
        'version_code': '370805',
        'version_name': '37.8.5',
        'device_platform': 'ios',
        'channel': 'appstore',
        'os': 'ios'
    }
}

# إعدادات البلاغات المحدثة والموثقة من TikTok
REPORT_REASONS = {
    # بلاغات الفيديو - محدثة حسب TikTok الحالي
    1001: "محتوى جنسي أو إباحي",
    1002: "عنف أو إيذاء",
    1003: "تحرش أو إساءة",
    1004: "معلومات كاذبة أو مضللة",
    1005: "انتحال شخصية",
    1006: "محتوى ضار أو خطير",
    1007: "إساءة أو تنمر",
    1008: "محتوى غير مناسب للأطفال",
    1009: "انتهاك حقوق الملكية",
    1010: "محتوى إرهابي أو متطرف",
    1011: "محتوى عنصري أو تمييزي",
    1012: "محتوى طبي خاطئ",
    1013: "محتوى مالي احتيالي",
    1014: "محتوى سياسي مسيء",
    1015: "محتوى ديني مسيء",
    1016: "محتوى تعليمي خاطئ",
    1017: "محتوى رياضي مسيء",
    1018: "محتوى ترفيهي ضار",
    1019: "محتوى تجاري مزعج",
    1020: "محتوى آخر"
}

# أنواع البلاغات حسب الفئة - محدثة
REPORT_CATEGORIES = {
    'video': {
        'sexual': [1001, 1008],
        'violent': [1002, 1006, 1010],
        'harassment': [1003, 1007],
        'misinformation': [1004, 1012, 1013, 1016],
        'impersonation': [1005],
        'copyright': [1009],
        'discrimination': [1011, 1014, 1015, 1017],
        'commercial': [1019],
        'other': [1018, 1020]
    },
    'account': {
        'spam': [1019],
        'fake': [1004, 1005, 1012, 1013],
        'harmful': [1001, 1002, 1003, 1006, 1007, 1010, 1011, 1014, 1015, 1017],
        'inappropriate': [1008, 1016, 1018],
        'other': [1020]
    }
}

# إعدادات الأجهزة المحدثة والموثقة
DEVICE_CONFIGS = {
    'android': {
        'versions': ['14', '13', '12', '11'],
        'api_levels': ['34', '33', '32', '30'],
        'brands': ['samsung', 'xiaomi', 'oneplus', 'huawei', 'oppo', 'vivo'],
        'models': {
            'samsung': ['SM-G991B', 'SM-G998B', 'SM-A546B', 'SM-F946B'],
            'xiaomi': ['Redmi Note 12 Pro', 'POCO F5', 'Mi 13T Pro'],
            'oneplus': ['OnePlus 11', 'OnePlus 10 Pro', 'OnePlus Nord 3'],
            'huawei': ['P60 Pro', 'Mate 60 Pro', 'Nova 11 Pro'],
            'oppo': ['Find X6 Pro', 'Reno 10 Pro+', 'A98 5G'],
            'vivo': ['X90 Pro+', 'V29 Pro', 'Y100']
        }
    },
    'ios': {
        'versions': ['17', '16', '15'],
        'models': ['iPhone 15 Pro', 'iPhone 14 Pro', 'iPhone 13 Pro', 'iPhone 12 Pro']
    }
}

# إعدادات السلوك البشري المحسن
HUMAN_DELAYS = {
    'min_delay': 3,
    'max_delay': 7,
    'typing_delay': 1.5,
    'action_delay': 2.5,
    'login_delay': 5,
    'report_delay': 4
}

# إعدادات الشبكة المحسنة
HTTP_TIMEOUT_SECONDS = int(os.getenv('HTTP_TIMEOUT_SECONDS', 45))
HTTP_MAX_RETRIES = int(os.getenv('HTTP_MAX_RETRIES', 3))
HTTP_BACKOFF_FACTOR = float(os.getenv('HTTP_BACKOFF_FACTOR', 0.8))
HTTP_PROXIES = os.getenv('HTTP_PROXIES', '')

# إعدادات Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# إعدادات التشفير
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-key-32-chars-long')

# إعدادات بوت تيليجرام
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
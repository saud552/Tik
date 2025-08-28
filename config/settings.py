import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات بوت تيليجرام
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

# إعدادات TikTok
TIKTOK_BASE_URL = "https://www.tiktok.com"
TIKTOK_API_BASE = "https://api16-normal-c-alisg.ttapis.com"
TIKTOK_MOBILE_API = "https://api-h2.tiktokv.com"

# إعدادات الشبكة والمهل والمحاولات
HTTP_TIMEOUT_SECONDS = int(os.getenv('HTTP_TIMEOUT_SECONDS', 30))
HTTP_MAX_RETRIES = int(os.getenv('HTTP_MAX_RETRIES', 2))
HTTP_BACKOFF_FACTOR = float(os.getenv('HTTP_BACKOFF_FACTOR', 0.5))
HTTP_PROXIES = os.getenv('HTTP_PROXIES', '')  # تنسيق: http://user:pass@host:port;https://user:pass@host:port

# إعدادات Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# إعدادات التشفير
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-key-32-chars-long')

# أنواع البلاغات المتاحة - محدثة ومرنة
REPORT_REASONS = {
    # بلاغات الفيديو
    1: "محتوى جنسي أو إباحي",
    2: "عنف أو إيذاء",
    3: "تحرش أو إساءة",
    4: "معلومات كاذبة أو مضللة",
    5: "انتحال شخصية",
    6: "محتوى ضار أو خطير",
    7: "إساءة أو تنمر",
    8: "محتوى غير مناسب للأطفال",
    9: "انتهاك حقوق الملكية",
    10: "محتوى إرهابي أو متطرف",
    11: "محتوى عنصري أو تمييزي",
    12: "محتوى طبي خاطئ",
    13: "محتوى مالي احتيالي",
    14: "محتوى سياسي مسيء",
    15: "محتوى ديني مسيء",
    16: "محتوى تعليمي خاطئ",
    17: "محتوى رياضي مسيء",
    18: "محتوى ترفيهي ضار",
    19: "محتوى تجاري مزعج",
    20: "محتوى آخر"
}

# أنواع البلاغات حسب الفئة
REPORT_CATEGORIES = {
    'video': {
        'sexual': [1, 8],
        'violent': [2, 6, 10],
        'harassment': [3, 7],
        'misinformation': [4, 12, 13, 16],
        'impersonation': [5],
        'copyright': [9],
        'discrimination': [11, 14, 15, 17],
        'commercial': [19],
        'other': [18, 20]
    },
    'account': {
        'spam': [19],
        'fake': [4, 5, 12, 13],
        'harmful': [1, 2, 3, 6, 7, 10, 11, 14, 15, 17],
        'inappropriate': [8, 16, 18],
        'other': [20]
    }
}

# إعدادات API محدثة
TIKTOK_API_ENDPOINTS = {
    'mobile': 'https://api-h2.tiktokv.com',
    'web': 'https://www.tiktok.com',
    'report': 'https://api16-normal-c-alisg.ttapis.com',
    'backup': 'https://api19-normal-c-useast1a.tiktokv.com'
}

# إعدادات الأجهزة المحدثة
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

# إعدادات السلوك البشري
HUMAN_DELAYS = {
    'min_delay': 2,
    'max_delay': 8,
    'typing_delay': 1,
    'action_delay': 3
}
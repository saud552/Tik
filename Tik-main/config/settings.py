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

# إعدادات Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# إعدادات التشفير
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-key-32-chars-long')

# أنواع البلاغات المتاحة
REPORT_REASONS = {
    1: "محتوى جنسي",
    2: "عنف",
    3: "تحرش",
    4: "معلومات كاذبة",
    5: "انتحال شخصية",
    6: "محتوى ضار",
    7: "إساءة",
    8: "محتوى غير مناسب",
    9: "انتهاك حقوق الملكية",
    10: "محتوى خطير"
}

# إعدادات السلوك البشري
HUMAN_DELAYS = {
    'min_delay': 2,
    'max_delay': 8,
    'typing_delay': 1,
    'action_delay': 3
}
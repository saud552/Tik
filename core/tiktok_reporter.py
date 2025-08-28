import requests
import time
import random
import re
import json
import uuid
import hashlib
from typing import Optional, Dict, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, parse_qs
from config.settings import (
    TIKTOK_BASE_URL,
    TIKTOK_MOBILE_API,
    TIKTOK_WEB_API,
    TIKTOK_PASSPORT_API,
    TIKTOK_API_ENDPOINTS,
    TIKTOK_APP_CONFIG,
    HUMAN_DELAYS,
    HTTP_TIMEOUT_SECONDS,
    HTTP_MAX_RETRIES,
    HTTP_BACKOFF_FACTOR,
    HTTP_PROXIES,
)
from models.account import TikTokAccount

class TikTokReporter:
    def __init__(self, account_manager=None):
        self.session = requests.Session()
        self.account_manager = account_manager
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        self.setup_session()
    
    def setup_session(self):
        """إعداد الجلسة مع إعدادات واقعية ومحدثة"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })

        # Configure retries and backoff
        retries = Retry(
            total=HTTP_MAX_RETRIES,
            backoff_factor=HTTP_BACKOFF_FACTOR,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Optional proxies from env
        if HTTP_PROXIES:
            # Support format "http://...;https://..."
            parts = [p.strip() for p in HTTP_PROXIES.split(";") if p.strip()]
            proxies: Dict[str, str] = {}
            for p in parts:
                if p.startswith("http://"):
                    proxies["http"] = p
                elif p.startswith("https://"):
                    proxies["https"] = p
            if proxies:
                self.session.proxies.update(proxies)
    
    def _simulate_human_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        """محاكاة تأخير بشري محسن"""
        if min_delay is None:
            min_delay = HUMAN_DELAYS['min_delay']
        if max_delay is None:
            max_delay = HUMAN_DELAYS['max_delay']
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _get_device_info(self) -> Dict[str, str]:
        """الحصول على معلومات الجهاز الواقعية والمحدثة"""
        devices = [
            {
                'device_type': 'SM-G991B',
                'device_brand': 'samsung',
                'os_version': '14',
                'os_api': '34',
                'resolution': '1080*2400',
                'dpi': '420'
            },
            {
                'device_type': 'Redmi Note 12 Pro',
                'device_brand': 'Redmi',
                'os_version': '13',
                'os_api': '33',
                'resolution': '1080*2400',
                'dpi': '395'
            },
            {
                'device_type': 'OnePlus 11',
                'device_brand': 'OnePlus',
                'os_version': '14',
                'os_api': '34',
                'resolution': '1440*3216',
                'dpi': '560'
            },
            {
                'device_type': 'iPhone 15 Pro',
                'device_brand': 'Apple',
                'os_version': '17',
                'os_api': '17',
                'resolution': '1179*2556',
                'dpi': '460'
            }
        ]
        return random.choice(devices)
    
    async def login_account(self, account: TikTokAccount) -> bool:
        """تسجيل دخول الحساب باستخدام TikTok API الحقيقي"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay(HUMAN_DELAYS['login_delay'], HUMAN_DELAYS['login_delay'] + 2)
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # الحصول على كلمة المرور
            password = self.account_manager.get_decrypted_password(account.id)
            if not password:
                print(f"❌ فشل في الحصول على كلمة المرور للحساب {account.username}")
                return False
            
            # محاولة 1: تسجيل الدخول عبر الويب (الأكثر موثوقية)
            if await self._web_login(account.id, account.username, password):
                print(f"✅ تم تسجيل الدخول بنجاح عبر الويب للحساب {account.username}")
                return True
            
            # محاولة 2: تسجيل الدخول عبر Mobile API
            if await self._mobile_login(account.id, account.username, password):
                print(f"✅ تم تسجيل الدخول بنجاح عبر Mobile API للحساب {account.username}")
                return True
            
            print(f"❌ فشل في تسجيل الدخول للحساب {account.username}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في تسجيل دخول الحساب {account.username}: {e}")
            return False
    
    async def _web_login(self, account_id: str, username: str, password: str) -> bool:
        """تسجيل الدخول عبر TikTok Web API"""
        try:
            # أولاً: الحصول على صفحة تسجيل الدخول للحصول على CSRF token
            login_page_url = f"{TIKTOK_PASSPORT_API}/web/login/"
            response = self.session.get(login_page_url, timeout=HTTP_TIMEOUT_SECONDS)
            
            if response.status_code != 200:
                print(f"❌ فشل في الوصول لصفحة تسجيل الدخول: {response.status_code}")
                return False
            
            # البحث عن CSRF token
            csrf_match = re.search(r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']', response.text)
            if not csrf_match:
                print("❌ لم يتم العثور على CSRF token")
                return False
            
            csrf_token = csrf_match.group(1)
            
            # بناء بيانات تسجيل الدخول
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token,
                'aid': TIKTOK_APP_CONFIG['web']['aid'],
                'app_name': TIKTOK_APP_CONFIG['web']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['web']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['web']['version_name'],
                'device_platform': TIKTOK_APP_CONFIG['web']['device_platform'],
                'channel': TIKTOK_APP_CONFIG['web']['channel']
            }
            
            # إرسال طلب تسجيل الدخول
            login_response = self.session.post(
                TIKTOK_API_ENDPOINTS['login'],
                data=login_data,
                timeout=HTTP_TIMEOUT_SECONDS,
                allow_redirects=True
            )
            
            # التحقق من نجاح تسجيل الدخول
            if login_response.status_code == 200:
                # التحقق من وجود كوكيز الجلسة
                session_cookies = ['sessionid', 'ttwid', 'tt_csrf_token']
                has_session = any(cookie in self.session.cookies for cookie in session_cookies)
                
                if has_session:
                    # حفظ الكوكيز
                    cookies = '; '.join([f'{k}={v}' for k, v in self.session.cookies.items()])
                    if self.account_manager:
                        self.account_manager.update_account_cookies(account_id, cookies)
                    return True
            
            print(f"❌ فشل في تسجيل الدخول عبر الويب: {login_response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في تسجيل الدخول عبر الويب: {e}")
            return False
    
    async def _mobile_login(self, account_id: str, username: str, password: str) -> bool:
        """تسجيل الدخول عبر TikTok Mobile API"""
        try:
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # بناء بيانات تسجيل الدخول
            login_data = {
                'username': username,
                'password': password,
                'mix_mode': '1',
                'type': '1',
                'device_platform': 'android',
                'aid': TIKTOK_APP_CONFIG['mobile_android']['aid'],
                'app_name': TIKTOK_APP_CONFIG['mobile_android']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['mobile_android']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['mobile_android']['version_name'],
                'channel': TIKTOK_APP_CONFIG['mobile_android']['channel'],
                'os': TIKTOK_APP_CONFIG['mobile_android']['os'],
                'device_type': device_info['device_type'],
                'device_brand': device_info['device_brand'],
                'os_version': device_info['os_version'],
                'os_api': device_info['os_api'],
                'resolution': device_info['resolution'],
                'dpi': device_info['dpi'],
                'cpu_abi': TIKTOK_APP_CONFIG['mobile_android']['cpu_abi'],
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000000000, 9999999999)),
                'device_id': str(random.randint(1000000000, 9999999999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000))
            }
            
            # إرسال طلب تسجيل الدخول
            response = self.session.post(
                TIKTOK_API_ENDPOINTS['login_mobile'],
                data=login_data,
                timeout=HTTP_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # التحقق من نجاح تسجيل الدخول
                    if result.get('status_code') == 0 and result.get('data', {}).get('user_id'):
                        # حفظ الكوكيز
                        cookies = '; '.join([f'{k}={v}' for k, v in self.session.cookies.items()])
                        if self.account_manager:
                            self.account_manager.update_account_cookies(account_id, cookies)
                        return True
                except json.JSONDecodeError:
                    pass
            
            print(f"❌ فشل في تسجيل الدخول عبر Mobile API: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في تسجيل الدخول عبر Mobile API: {e}")
            return False
    
    def _normalize_tiktok_url(self, url: str) -> str:
        """تطبيع روابط TikTok وإزالة المعاملات غير الضرورية"""
        try:
            # تنظيف الرابط
            url = url.strip()
            
            # إضافة https:// إذا لم يكن موجوداً
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # إزالة المعاملات غير الضرورية
            if '?' in url:
                base_url = url.split('?')[0]
                # الاحتفاظ بمعاملات مهمة فقط
                query_params = parse_qs(url.split('?')[1])
                important_params = ['video', 'user', 't']
                filtered_params = {k: v for k, v in query_params.items() if k in important_params}
                
                if filtered_params:
                    param_strings = [f"{k}={v[0]}" for k, v in filtered_params.items()]
                    url = base_url + '?' + '&'.join(param_strings)
                else:
                    url = base_url
            
            return url
        except Exception as e:
            print(f"❌ خطأ في تطبيع الرابط: {e}")
            return url
    
    def _extract_video_id_advanced(self, video_url: str) -> Optional[str]:
        """استخراج معرف الفيديو بطريقة متقدمة ومتعددة الأنماط"""
        try:
            # تطبيع الرابط
            normalized_url = self._normalize_tiktok_url(video_url)
            
            # أنماط مختلفة لمعرف الفيديو
            video_patterns = [
                r'/video/(\d+)',  # النمط الأساسي
                r'/v/(\d+)',      # نمط مختصر
                r'video/(\d+)',   # بدون /
                r'v/(\d+)',       # نمط مختصر بدون /
                r'@[^/]+/video/(\d+)',  # مع اسم المستخدم
                r'video/(\d+)\?',  # مع معاملات
                r'/(\d{19})',      # معرف طويل (19 رقم)
                r'/(\d{17,19})',   # معرف طويل (17-19 رقم)
            ]
            
            for pattern in video_patterns:
                match = re.search(pattern, normalized_url)
                if match:
                    video_id = match.group(1)
                    # التحقق من أن المعرف رقمي
                    if video_id.isdigit():
                        return video_id
            
            return None
            
        except Exception as e:
            print(f"❌ خطأ في استخراج معرف الفيديو: {e}")
            return None
    
    def _extract_username_advanced(self, url: str) -> Optional[str]:
        """استخراج اسم المستخدم بطريقة متقدمة"""
        try:
            # تطبيع الرابط
            normalized_url = self._normalize_tiktok_url(url)
            
            # أنماط مختلفة لاسم المستخدم
            username_patterns = [
                r'@([^/]+)',           # @username
                r'tiktok\.com/@([^/]+)',  # tiktok.com/@username
                r'vm\.tiktok\.com/@([^/]+)',  # vm.tiktok.com/@username
                r'vt\.tiktok\.com/@([^/]+)',  # vt.tiktok.com/@username
                r'([a-zA-Z0-9._-]+)',  # username بدون @
            ]
            
            for pattern in username_patterns:
                match = re.search(pattern, normalized_url)
                if match:
                    username = match.group(1)
                    # التحقق من صحة اسم المستخدم
                    if self._is_valid_username(username):
                        return username
            
            return None
            
        except Exception as e:
            print(f"❌ خطأ في استخراج اسم المستخدم: {e}")
            return None
    
    def _is_valid_username(self, username: str) -> bool:
        """التحقق من صحة اسم المستخدم"""
        if not username:
            return False
        
        # قواعد صحة اسم المستخدم
        if len(username) < 3 or len(username) > 24:
            return False
        
        # يجب أن يحتوي على أحرف وأرق فقط
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            return False
        
        # لا يمكن أن يبدأ أو ينتهي بـ .
        if username.startswith('.') or username.endswith('.'):
            return False
        
        return True
    
    async def extract_video_info(self, video_url: str) -> Tuple[Optional[str], Optional[str]]:
        """استخراج معلومات الفيديو بطريقة محسنة ومتعددة الأنماط"""
        try:
            # تطبيع الرابط
            normalized_url = self._normalize_tiktok_url(video_url)
            
            # استخراج معرف الفيديو
            video_id = self._extract_video_id_advanced(normalized_url)
            if not video_id:
                print(f"❌ فشل في استخراج معرف الفيديو من: {video_url}")
                return None, None
            
            # استخراج اسم المستخدم
            username = self._extract_username_advanced(normalized_url)
            if not username:
                print(f"❌ فشل في استخراج اسم المستخدم من: {video_url}")
                return None, None
            
            # التحقق من وجود الفيديو فعلياً
            if not await self._verify_video_exists(video_id, username):
                print(f"❌ الفيديو غير موجود أو تم حذفه: {video_id}")
                return None, None
            
            # الحصول على معرف المستخدم
            user_id = await self._get_user_id_advanced(username)
            if not user_id:
                print(f"❌ فشل في الحصول على معرف المستخدم: {username}")
                return None, None
            
            return video_id, user_id
            
        except Exception as e:
            print(f"❌ خطأ في استخراج معلومات الفيديو: {e}")
            return None, None
    
    async def _verify_video_exists(self, video_id: str, username: str) -> bool:
        """التحقق من وجود الفيديو فعلياً باستخدام TikTok API"""
        try:
            # محاولة 1: التحقق عبر Mobile API
            mobile_url = f"{TIKTOK_MOBILE_API}/aweme/v1/aweme/detail/"
            mobile_params = {
                'aweme_id': video_id,
                'aid': TIKTOK_APP_CONFIG['mobile_android']['aid'],
                'app_name': TIKTOK_APP_CONFIG['mobile_android']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['mobile_android']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['mobile_android']['version_name'],
                'device_platform': 'android',
                'channel': 'googleplay'
            }
            
            response = self.session.get(mobile_url, params=mobile_params, timeout=HTTP_TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status_code') == 0 and result.get('aweme_detail'):
                        print(f"✅ تم التحقق من وجود الفيديو {video_id} عبر Mobile API")
                        return True
                except json.JSONDecodeError:
                    pass
            
            # محاولة 2: التحقق عبر الويب
            web_url = f"{TIKTOK_BASE_URL}/@{username}/video/{video_id}"
            web_response = self.session.get(web_url, timeout=HTTP_TIMEOUT_SECONDS, allow_redirects=True)
            
            if web_response.status_code == 200:
                content = web_response.text.lower()
                
                # مؤشرات وجود الفيديو
                video_indicators = [
                    'video-player',
                    'video-container',
                    'video-player-container',
                    'tiktok-video',
                    'video-js',
                    'video-player-wrapper',
                    'aweme-detail',
                    'video-detail'
                ]
                
                for indicator in video_indicators:
                    if indicator in content:
                        print(f"✅ تم التحقق من وجود الفيديو {video_id} عبر الويب")
                        return True
                
                # التحقق من عدم وجود رسائل خطأ
                error_indicators = [
                    'video not found',
                    'video unavailable',
                    'video removed',
                    'content not available',
                    'page not found',
                    '404',
                    'error',
                    'unavailable'
                ]
                
                for error in error_indicators:
                    if error in content:
                        print(f"❌ الفيديو {video_id} غير متاح")
                        return False
            
            print(f"⚠️ لم يتم التأكد من وجود الفيديو {video_id}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في التحقق من وجود الفيديو: {e}")
            return False
    
    async def _get_user_id_advanced(self, username: str) -> Optional[str]:
        """الحصول على معرف المستخدم بطريقة متقدمة"""
        try:
            # محاولة 1: عبر Mobile API
            mobile_url = f"{TIKTOK_MOBILE_API}/user/detail/"
            mobile_params = {
                'unique_id': username,
                'aid': TIKTOK_APP_CONFIG['mobile_android']['aid'],
                'app_name': TIKTOK_APP_CONFIG['mobile_android']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['mobile_android']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['mobile_android']['version_name'],
                'device_platform': 'android',
                'channel': 'googleplay'
            }
            
            response = self.session.get(mobile_url, params=mobile_params, timeout=HTTP_TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('status_code') == 0 and result.get('user_info', {}).get('uid'):
                        user_id = result['user_info']['uid']
                        print(f"✅ تم الحصول على معرف المستخدم {username}: {user_id} عبر Mobile API")
                        return user_id
                except json.JSONDecodeError:
                    pass
            
            # محاولة 2: عبر الويب
            web_url = f"{TIKTOK_BASE_URL}/@{username}"
            web_response = self.session.get(web_url, timeout=HTTP_TIMEOUT_SECONDS, allow_redirects=True)
            
            if web_response.status_code == 200:
                content = web_response.text
                
                # طريقة 1: البحث في HTML
                user_id_match = re.search(r'"id":"(\d+)"', content)
                if user_id_match:
                    user_id = user_id_match.group(1)
                    print(f"✅ تم الحصول على معرف المستخدم {username}: {user_id} عبر الويب")
                    return user_id
                
                # طريقة 2: البحث في JSON
                json_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', content)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        # استخراج معرف المستخدم من البيانات
                        user_info = data.get('UserModule', {}).get('users', {}).get(username, {})
                        if user_info and 'id' in user_info:
                            user_id = user_info['id']
                            print(f"✅ تم الحصول على معرف المستخدم {username}: {user_id} عبر SIGI_STATE")
                            return user_id
                    except Exception:
                        pass
                
                # طريقة 3: البحث في meta tags
                meta_match = re.search(r'<meta property="al:ios:url" content="tiktok://user/(\d+)"', content)
                if meta_match:
                    user_id = meta_match.group(1)
                    print(f"✅ تم الحصول على معرف المستخدم {username}: {user_id} عبر meta tags")
                    return user_id
                
                # طريقة 4: البحث في JavaScript
                js_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', content)
                if js_match:
                    try:
                        data = json.loads(js_match.group(1))
                        # البحث في البيانات
                        if 'user' in data and 'id' in data['user']:
                            user_id = data['user']['id']
                            print(f"✅ تم الحصول على معرف المستخدم {username}: {user_id} عبر __INITIAL_STATE__")
                            return user_id
                    except Exception:
                        pass
            
            print(f"❌ فشل في الحصول على معرف المستخدم: {username}")
            return None
            
        except Exception as e:
            print(f"❌ خطأ في الحصول على معرف المستخدم: {e}")
            return None
    
    async def report_video(self, account: TikTokAccount, video_id: str, user_id: str, reason: int) -> bool:
        """إبلاغ عن فيديو باستخدام TikTok API الحقيقي"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay(HUMAN_DELAYS['report_delay'], HUMAN_DELAYS['report_delay'] + 2)
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # محاولة الإبلاغ عبر API محدث
            success = False
            
            # API 1: Mobile API (الأكثر موثوقية)
            try:
                success = await self._report_video_mobile(video_id, user_id, reason, device_info)
                if success:
                    print(f"✅ تم الإبلاغ عن الفيديو {video_id} بنجاح عبر Mobile API")
                    account.mark_success()
                    return True
            except Exception as e:
                print(f"❌ فشل في Mobile API: {e}")
            
            # API 2: Web API
            if not success:
                try:
                    success = await self._report_video_web(video_id, user_id, reason)
                    if success:
                        print(f"✅ تم الإبلاغ عن الفيديو {video_id} بنجاح عبر Web API")
                        account.mark_success()
                        return True
                except Exception as e:
                    print(f"❌ فشل في Web API: {e}")
            
            if not success:
                error_msg = "فشل في جميع محاولات الإبلاغ"
                account.mark_failure(error_msg)
                print(f"❌ {error_msg}")
                return False
            
            return success
            
        except Exception as e:
            error_msg = f"خطأ في إبلاغ الفيديو: {e}"
            account.mark_failure(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def _report_video_mobile(self, video_id: str, user_id: str, reason: int, device_info: Dict[str, str]) -> bool:
        """الإبلاغ عن الفيديو عبر Mobile API"""
        try:
            # بناء بيانات البلاغ
            report_data = {
                'aweme_id': video_id,
                'owner_id': user_id,
                'reason': str(reason),
                'report_desc': '',
                'device_platform': 'android',
                'os': 'android',
                'device_type': device_info['device_type'],
                'device_brand': device_info['device_brand'],
                'os_version': device_info['os_version'],
                'os_api': device_info['os_api'],
                'resolution': device_info['resolution'],
                'dpi': device_info['dpi'],
                'channel': 'googleplay',
                'aid': TIKTOK_APP_CONFIG['mobile_android']['aid'],
                'app_name': TIKTOK_APP_CONFIG['mobile_android']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['mobile_android']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['mobile_android']['version_name'],
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000000000, 9999999999)),
                'device_id': str(random.randint(1000000000, 9999999999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000)),
                'manifest_version_code': '2024120100',
                'update_version_code': '2024120100',
                'channel_sdk_version': '2024120100',
                'language': 'en',
                'cpu_abi': 'arm64-v8a',
                'asr_id': str(random.randint(1000000000, 9999999999)),
                'channel_id': 'googleplay',
                'idfa': str(uuid.uuid4()),
                'install_id': str(uuid.uuid4())
            }
            
            # إرسال البلاغ
            response = self.session.post(
                TIKTOK_API_ENDPOINTS['report_video'],
                data=report_data,
                timeout=HTTP_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # التحقق من نجاح البلاغ
                    if result.get('status_code') == 0:
                        return True
                    else:
                        print(f"❌ فشل في البلاغ: {result.get('status_msg', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print("❌ استجابة غير صحيحة من API")
                    return False
            
            print(f"❌ فشل في البلاغ: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في Mobile API: {e}")
            return False
    
    async def _report_video_web(self, video_id: str, user_id: str, reason: int) -> bool:
        """الإبلاغ عن الفيديو عبر Web API"""
        try:
            # التأكد من وجود كوكيز جلسة لازمة قبل محاولة الإبلاغ عبر الويب
            required_cookies = ['ttwid', 'tt_csrf_token']
            if not any(cookie in self.session.cookies for cookie in required_cookies):
                print("❌ لا توجد كوكيز جلسة صالحة للإبلاغ عبر الويب")
                return False
            # بناء بيانات البلاغ
            report_data = {
                'aweme_id': video_id,
                'owner_id': user_id,
                'reason': str(reason),
                'report_desc': '',
                'device_platform': 'webapp',
                'aid': TIKTOK_APP_CONFIG['web']['aid'],
                'app_name': TIKTOK_APP_CONFIG['web']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['web']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['web']['version_name']
            }
            
            # إرسال البلاغ
            response = self.session.post(
                TIKTOK_API_ENDPOINTS['report_web'],
                data=report_data,
                timeout=HTTP_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # التحقق من نجاح البلاغ
                    if result.get('status_code') == 0 or result.get('success') is True:
                        return True
                    else:
                        print(f"❌ فشل في البلاغ: {result.get('message', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print("❌ استجابة غير صحيحة من Web API (ليست JSON صحيحة)")
                    return False
            
            print(f"❌ فشل في البلاغ: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في Web API: {e}")
            return False
    
    async def report_account(self, account: TikTokAccount, target_username: str, reason: int) -> bool:
        """إبلاغ عن حساب باستخدام TikTok API الحقيقي"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay(HUMAN_DELAYS['report_delay'], HUMAN_DELAYS['report_delay'] + 2)
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # الحصول على معرف المستخدم المستهدف
            target_user_id = await self._get_user_id_advanced(target_username)
            if not target_user_id:
                account.mark_failure("فشل في الحصول على معرف المستخدم المستهدف")
                return False
            
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # محاولة الإبلاغ عبر API محدث
            success = False
            
            # API 1: Mobile API
            try:
                success = await self._report_account_mobile(target_user_id, reason, device_info)
                if success:
                    print(f"✅ تم الإبلاغ عن الحساب {target_username} بنجاح عبر Mobile API")
                    account.mark_success()
                    return True
            except Exception as e:
                print(f"❌ فشل في Mobile API: {e}")
            
            # API 2: Web API
            if not success:
                try:
                    success = await self._report_account_web(target_user_id, reason)
                    if success:
                        print(f"✅ تم الإبلاغ عن الحساب {target_username} بنجاح عبر Web API")
                        account.mark_success()
                        return True
                except Exception as e:
                    print(f"❌ فشل في Web API: {e}")
            
            if not success:
                error_msg = "فشل في جميع محاولات الإبلاغ"
                account.mark_failure(error_msg)
                print(f"❌ {error_msg}")
                return False
            
            return success
            
        except Exception as e:
            error_msg = f"خطأ في إبلاغ الحساب: {e}"
            account.mark_failure(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def _report_account_mobile(self, user_id: str, reason: int, device_info: Dict[str, str]) -> bool:
        """الإبلاغ عن الحساب عبر Mobile API"""
        try:
            # بناء بيانات البلاغ
            report_data = {
                'user_id': user_id,
                'reason': str(reason),
                'report_desc': '',
                'device_platform': 'android',
                'os': 'android',
                'device_type': device_info['device_type'],
                'device_brand': device_info['device_brand'],
                'os_version': device_info['os_version'],
                'os_api': device_info['os_api'],
                'resolution': device_info['resolution'],
                'dpi': device_info['dpi'],
                'channel': 'googleplay',
                'aid': TIKTOK_APP_CONFIG['mobile_android']['aid'],
                'app_name': TIKTOK_APP_CONFIG['mobile_android']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['mobile_android']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['mobile_android']['version_name'],
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000000000, 9999999999)),
                'device_id': str(random.randint(1000000000, 9999999999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000)),
                'manifest_version_code': '2024120100',
                'update_version_code': '2024120100',
                'channel_sdk_version': '2024120100',
                'language': 'en',
                'cpu_abi': 'arm64-v8a',
                'asr_id': str(random.randint(1000000000, 9999999999)),
                'channel_id': 'googleplay',
                'idfa': str(uuid.uuid4()),
                'install_id': str(uuid.uuid4())
            }
            
            # إرسال البلاغ
            response = self.session.post(
                TIKTOK_API_ENDPOINTS['report_user'],
                data=report_data,
                timeout=HTTP_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # التحقق من نجاح البلاغ
                    if result.get('status_code') == 0:
                        return True
                    else:
                        print(f"❌ فشل في البلاغ: {result.get('status_msg', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print("❌ استجابة غير صحيحة من API")
                    return False
            
            print(f"❌ فشل في البلاغ: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في Mobile API: {e}")
            return False
    
    async def _report_account_web(self, user_id: str, reason: int) -> bool:
        """الإبلاغ عن الحساب عبر Web API"""
        try:
            # التأكد من وجود كوكيز جلسة لازمة قبل محاولة الإبلاغ عبر الويب
            required_cookies = ['ttwid', 'tt_csrf_token']
            if not any(cookie in self.session.cookies for cookie in required_cookies):
                print("❌ لا توجد كوكيز جلسة صالحة للإبلاغ عبر الويب")
                return False
            # بناء بيانات البلاغ
            report_data = {
                'user_id': user_id,
                'reason': str(reason),
                'report_desc': '',
                'device_platform': 'webapp',
                'aid': TIKTOK_APP_CONFIG['web']['aid'],
                'app_name': TIKTOK_APP_CONFIG['web']['app_name'],
                'version_code': TIKTOK_APP_CONFIG['web']['version_code'],
                'version_name': TIKTOK_APP_CONFIG['web']['version_name']
            }
            
            # إرسال البلاغ
            response = self.session.post(
                f"{TIKTOK_API_ENDPOINTS['report_web']}/user/",
                data=report_data,
                timeout=HTTP_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    # التحقق من نجاح البلاغ
                    if result.get('status_code') == 0 or result.get('success') is True:
                        return True
                    else:
                        print(f"❌ فشل في البلاغ: {result.get('message', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    print("❌ استجابة غير صحيحة من Web API (ليست JSON صحيحة)")
                    return False
            
            print(f"❌ فشل في البلاغ: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ خطأ في Web API: {e}")
            return False
    
    def validate_target(self, target: str) -> Tuple[str, Optional[str], Optional[str]]:
        """التحقق من صحة الهدف وتحديد نوعه بطريقة محسنة"""
        target = target.strip()
        
        try:
            # تطبيع الرابط
            normalized_target = self._normalize_tiktok_url(target)
            
            # التحقق من أن الرابط يوجه إلى TikTok
            if not self._is_tiktok_url(normalized_target):
                return 'unknown', None, None
            
            # فحص نوع المحتوى
            if '/video/' in normalized_target or '/v/' in normalized_target:
                # فيديو
                video_id = self._extract_video_id_advanced(normalized_target)
                if not video_id:
                    return 'unknown', None, None
                
                username = self._extract_username_advanced(normalized_target)
                if not username:
                    return 'unknown', None, None
                
                return 'video', video_id, username
                
            elif target.startswith('@') or '@' in normalized_target or self._is_valid_username(target.replace('@', '').split('/')[0]):
                # حساب
                username = self._extract_username_advanced(normalized_target)
                if not username:
                    return 'unknown', None, None
                
                return 'account', username, None
            else:
                # محاولة استخراج كاسم مستخدم
                if self._is_valid_username(target):
                    return 'account', target, None
        
        except Exception as e:
            print(f"خطأ في التحقق من صحة الهدف: {e}")
        
        return 'unknown', None, None
    
    def _is_tiktok_url(self, url: str) -> bool:
        """التحقق من أن الرابط يوجه إلى TikTok"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            tiktok_domains = [
                'tiktok.com',
                'www.tiktok.com',
                'vm.tiktok.com',
                'vt.tiktok.com',
                'm.tiktok.com',
                'tiktokv.com',
                'www.tiktokv.com'
            ]
            
            return domain in tiktok_domains
            
        except Exception:
            return False
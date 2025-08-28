import requests
import time
import random
import re
import json
import uuid
from typing import Optional, Dict, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, parse_qs
from config.settings import (
    TIKTOK_BASE_URL,
    TIKTOK_API_BASE,
    TIKTOK_MOBILE_API,
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
        """تسجيل دخول الحساب مع تحسينات الأمان"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay()
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # محاولة تسجيل الدخول عبر API محدث
            password = self.account_manager.get_decrypted_password(account.id)
            if not password:
                return False
                
            login_data = {
                'username': account.username,
                'password': password,
                'mix_mode': '1',
                'type': '1',
                'webcast_sdk_version': '2201-3.4.2',
                'channel': 'tiktok_web',
                'device_platform': 'webapp',
                'aid': '1988',
                'app_name': 'tiktok_web',
                'version_code': '220100',
                'version_name': '22.1.0'
            }
            
            response = self.session.post(
                f"{TIKTOK_BASE_URL}/passport/web/login/",
                data=login_data,
                timeout=HTTP_TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                # حفظ الكوكيز
                cookies = '; '.join([f'{k}={v}' for k, v in self.session.cookies.items()])
                # تحديث الكوكيز في مدير الحسابات
                if self.account_manager:
                    self.account_manager.update_account_cookies(account.id, cookies)
                return True
            
            return False
            
        except Exception as e:
            print(f"خطأ في تسجيل دخول الحساب {account.username}: {e}")
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
            print(f"خطأ في تطبيع الرابط: {e}")
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
            print(f"خطأ في استخراج معرف الفيديو: {e}")
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
            print(f"خطأ في استخراج اسم المستخدم: {e}")
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
    
    def extract_video_info(self, video_url: str) -> Tuple[Optional[str], Optional[str]]:
        """استخراج معلومات الفيديو بطريقة محسنة ومتعددة الأنماط"""
        try:
            # تطبيع الرابط
            normalized_url = self._normalize_tiktok_url(video_url)
            
            # استخراج معرف الفيديو
            video_id = self._extract_video_id_advanced(normalized_url)
            if not video_id:
                print(f"فشل في استخراج معرف الفيديو من: {video_url}")
                return None, None
            
            # استخراج اسم المستخدم
            username = self._extract_username_advanced(normalized_url)
            if not username:
                print(f"فشل في استخراج اسم المستخدم من: {video_url}")
                return None, None
            
            # التحقق من وجود الفيديو فعلياً
            if not await self._verify_video_exists(video_id, username):
                print(f"الفيديو غير موجود أو تم حذفه: {video_id}")
                return None, None
            
            # الحصول على معرف المستخدم
            user_id = await self._get_user_id_advanced(username)
            if not user_id:
                print(f"فشل في الحصول على معرف المستخدم: {username}")
                return None, None
            
            return video_id, user_id
            
        except Exception as e:
            print(f"خطأ في استخراج معلومات الفيديو: {e}")
            return None, None
    
    async def _verify_video_exists(self, video_id: str, username: str) -> bool:
        """التحقق من وجود الفيديو فعلياً"""
        try:
            # محاولة الوصول إلى صفحة الفيديو
            video_url = f"{TIKTOK_BASE_URL}/@{username}/video/{video_id}"
            
            response = self.session.get(
                video_url,
                timeout=HTTP_TIMEOUT_SECONDS,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                # التحقق من أن الصفحة تحتوي على محتوى الفيديو
                content = response.text.lower()
                
                # مؤشرات وجود الفيديو
                video_indicators = [
                    'video-player',
                    'video-container',
                    'video-player-container',
                    'tiktok-video',
                    'video-js',
                    'video-player-wrapper'
                ]
                
                for indicator in video_indicators:
                    if indicator in content:
                        return True
                
                # التحقق من عدم وجود رسائل خطأ
                error_indicators = [
                    'video not found',
                    'video unavailable',
                    'video removed',
                    'content not available',
                    'page not found',
                    '404'
                ]
                
                for error in error_indicators:
                    if error in content:
                        return False
                
                # إذا لم نجد مؤشرات واضحة، نفترض أن الفيديو موجود
                return True
            
            return False
            
        except Exception as e:
            print(f"خطأ في التحقق من وجود الفيديو: {e}")
            return False
    
    async def _get_user_id_advanced(self, username: str) -> Optional[str]:
        """الحصول على معرف المستخدم بطريقة متقدمة"""
        try:
            # محاولة الوصول إلى صفحة المستخدم
            user_url = f"{TIKTOK_BASE_URL}/@{username}"
            
            response = self.session.get(
                user_url,
                timeout=HTTP_TIMEOUT_SECONDS,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                content = response.text
                
                # طريقة 1: البحث في HTML
                user_id_match = re.search(r'"id":"(\d+)"', content)
                if user_id_match:
                    return user_id_match.group(1)
                
                # طريقة 2: البحث في JSON
                json_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', content)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        # استخراج معرف المستخدم من البيانات
                        user_info = data.get('UserModule', {}).get('users', {}).get(username, {})
                        if user_info and 'id' in user_info:
                            return user_info['id']
                    except Exception:
                        pass
                
                # طريقة 3: البحث في meta tags
                meta_match = re.search(r'<meta property="al:ios:url" content="tiktok://user/(\d+)"', content)
                if meta_match:
                    return meta_match.group(1)
                
                # طريقة 4: البحث في JavaScript
                js_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', content)
                if js_match:
                    try:
                        data = json.loads(js_match.group(1))
                        # البحث في البيانات
                        if 'user' in data and 'id' in data['user']:
                            return data['user']['id']
                    except Exception:
                        pass
            
            return None
            
        except Exception as e:
            print(f"خطأ في الحصول على معرف المستخدم: {e}")
            return None
    
    async def report_video(self, account: TikTokAccount, video_id: str, user_id: str, reason: int) -> bool:
        """إبلاغ عن فيديو باستخدام API محدث"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay()
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # بناء بيانات البلاغ المحدثة
            report_data = {
                'report_type': 'video',
                'object_id': video_id,
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
                'aid': '1233',
                'app_name': 'tiktok',
                'version_code': '370805',
                'version_name': '37.8.5',
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000, 9999)),
                'device_id': str(random.randint(1000, 9999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000)),
                'manifest_version_code': '2024120100',
                'update_version_code': '2024120100',
                'channel_sdk_version': '2024120100',
                'device_platform': 'android',
                'device_type': device_info['device_type'],
                'language': 'en',
                'cpu_abi': 'arm64-v8a',
                'resolution': device_info['resolution'],
                'openudid': str(uuid.uuid4()),
                'update_version_code': '2024120100',
                '_rticket': str(int(time.time() * 1000)),
                'ts': str(int(time.time())),
                'asr_id': str(random.randint(1000000000, 9999999999)),
                'channel_id': 'googleplay',
                'device_id': str(random.randint(1000000000, 9999999999)),
                'iid': str(random.randint(1000000000, 9999999999)),
                'idfa': str(uuid.uuid4()),
                'install_id': str(uuid.uuid4()),
                'manifest_version_code': '2024120100',
                'openudid': str(uuid.uuid4()),
                'os_api': device_info['os_api'],
                'os_version': device_info['os_version'],
                'os': 'android',
                'device_platform': 'android',
                'device_type': device_info['device_type'],
                'device_brand': device_info['device_brand'],
                'resolution': device_info['resolution'],
                'dpi': device_info['dpi'],
                'app_name': 'tiktok',
                'version_code': '370805',
                'version_name': '37.8.5',
                'channel': 'googleplay',
                'aid': '1233',
                'app_name': 'tiktok',
                'version_code': '370805',
                'version_name': '37.8.5',
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000, 9999)),
                'device_id': str(random.randint(1000, 9999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000))
            }
            
            # محاولة الإبلاغ عبر API محدث
            success = False
            
            # API 1: API الرسمي المحدث
            try:
                response = self.session.post(
                    f"{TIKTOK_MOBILE_API}/aweme/v2/aweme/feedback/",
                    data=report_data,
                    timeout=HTTP_TIMEOUT_SECONDS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('status_code') == 0
                    
                    if success:
                        account.mark_success()
                        return True
            except Exception as e:
                print(f"فشل في API الأول: {e}")
            
            # API 2: API البديل
            if not success:
                try:
                    response = self.session.post(
                        f"{TIKTOK_API_BASE}/aweme/v2/aweme/feedback/",
                        data=report_data,
                        timeout=HTTP_TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        success = result.get('status_code') == 0
                        
                        if success:
                            account.mark_success()
                            return True
                except Exception as e:
                    print(f"فشل في API الثاني: {e}")
            
            # API 3: API الويب
            if not success:
                try:
                    web_report_data = {
                        'report_type': 'video',
                        'object_id': video_id,
                        'reason': str(reason),
                        'report_desc': '',
                        'device_platform': 'webapp',
                        'aid': '1988',
                        'app_name': 'tiktok_web',
                        'version_code': '220100',
                        'version_name': '22.1.0'
                    }
                    
                    response = self.session.post(
                        f"{TIKTOK_BASE_URL}/report/",
                        data=web_report_data,
                        timeout=HTTP_TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 200:
                        success = True
                        account.mark_success()
                        return True
                except Exception as e:
                    print(f"فشل في API الثالث: {e}")
            
            if not success:
                account.mark_failure("فشل في جميع محاولات الإبلاغ")
                return False
            
            return success
            
        except Exception as e:
            error_msg = f"خطأ في إبلاغ الفيديو: {e}"
            account.mark_failure(error_msg)
            print(error_msg)
            return False
    
    async def report_account(self, account: TikTokAccount, target_username: str, reason: int) -> bool:
        """إبلاغ عن حساب باستخدام API محدث"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay()
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # الحصول على معرف المستخدم المستهدف
            target_user_id = await self._get_user_id_advanced(target_username)
            if not target_user_id:
                account.mark_failure("فشل في الحصول على معرف المستخدم المستهدف")
                return False
            
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # بناء بيانات البلاغ المحدثة
            report_data = {
                'report_type': 'user',
                'object_id': target_user_id,
                'owner_id': target_user_id,
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
                'aid': '1233',
                'app_name': 'tiktok',
                'version_code': '370805',
                'version_name': '37.8.5',
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000, 9999)),
                'device_id': str(random.randint(1000, 9999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000)),
                'manifest_version_code': '2024120100',
                'update_version_code': '2024120100',
                'channel_sdk_version': '2024120100',
                'device_platform': 'android',
                'device_type': device_info['device_type'],
                'language': 'en',
                'cpu_abi': 'arm64-v8a',
                'resolution': device_info['resolution'],
                'openudid': str(uuid.uuid4()),
                'update_version_code': '2024120100',
                '_rticket': str(int(time.time() * 1000)),
                'ts': str(int(time.time())),
                'asr_id': str(random.randint(1000000000, 9999999999)),
                'channel_id': 'googleplay',
                'device_id': str(random.randint(1000000000, 9999999999)),
                'iid': str(random.randint(1000000000, 9999999999)),
                'idfa': str(uuid.uuid4()),
                'install_id': str(uuid.uuid4()),
                'manifest_version_code': '2024120100',
                'openudid': str(uuid.uuid4()),
                'os_api': device_info['os_api'],
                'os_version': device_info['os_version'],
                'os': 'android',
                'device_platform': 'android',
                'device_type': device_info['device_type'],
                'device_brand': device_info['device_brand'],
                'resolution': device_info['resolution'],
                'dpi': device_info['dpi'],
                'app_name': 'tiktok',
                'version_code': '370805',
                'version_name': '37.8.5',
                'channel': 'googleplay',
                'aid': '1233',
                'app_name': 'tiktok',
                'version_code': '370805',
                'version_name': '37.8.5',
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000, 9999)),
                'device_id': str(random.randint(1000, 9999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000))
            }
            
            # محاولة الإبلاغ عبر API محدث
            success = False
            
            # API 1: API الرسمي المحدث
            try:
                response = self.session.post(
                    f"{TIKTOK_MOBILE_API}/aweme/v2/aweme/feedback/",
                    data=report_data,
                    timeout=HTTP_TIMEOUT_SECONDS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('status_code') == 0
                    
                    if success:
                        account.mark_success()
                        return True
            except Exception as e:
                print(f"فشل في API الأول: {e}")
            
            # API 2: API البديل
            if not success:
                try:
                    response = self.session.post(
                        f"{TIKTOK_API_BASE}/aweme/v2/aweme/feedback/",
                        data=report_data,
                        timeout=HTTP_TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        success = result.get('status_code') == 0
                        
                        if success:
                            account.mark_success()
                            return True
                except Exception as e:
                    print(f"فشل في API الثاني: {e}")
            
            # API 3: API الويب
            if not success:
                try:
                    web_report_data = {
                        'report_type': 'user',
                        'object_id': target_user_id,
                        'reason': str(reason),
                        'report_desc': '',
                        'device_platform': 'webapp',
                        'aid': '1988',
                        'app_name': 'tiktok_web',
                        'version_code': '220100',
                        'version_name': '22.1.0'
                    }
                    
                    response = self.session.post(
                        f"{TIKTOK_BASE_URL}/report/user/",
                        data=web_report_data,
                        timeout=HTTP_TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 200:
                        success = True
                        account.mark_success()
                        return True
                except Exception as e:
                    print(f"فشل في API الثالث: {e}")
            
            if not success:
                account.mark_failure("فشل في جميع محاولات الإبلاغ")
                return False
            
            return success
            
        except Exception as e:
            error_msg = f"خطأ في إبلاغ الحساب: {e}"
            account.mark_failure(error_msg)
            print(error_msg)
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
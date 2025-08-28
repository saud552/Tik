import requests
import time
import random
import re
import json
import uuid
from typing import Optional, Dict, Tuple
from config.settings import TIKTOK_BASE_URL, TIKTOK_API_BASE, HUMAN_DELAYS
from models.account import TikTokAccount

class TikTokReporter:
    def __init__(self, account_manager=None):
        self.session = requests.Session()
        self.account_manager = account_manager
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.setup_session()
    
    def setup_session(self):
        """إعداد الجلسة مع إعدادات واقعية"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en:q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _simulate_human_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        """محاكاة تأخير بشري"""
        if min_delay is None:
            min_delay = HUMAN_DELAYS['min_delay']
        if max_delay is None:
            max_delay = HUMAN_DELAYS['max_delay']
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _get_device_info(self) -> Dict[str, str]:
        """الحصول على معلومات الجهاز الواقعية"""
        devices = [
            {
                'device_type': 'SM-G973F',
                'device_brand': 'samsung',
                'os_version': '11',
                'os_api': '30',
                'resolution': '1080*2340',
                'dpi': '420'
            },
            {
                'device_type': 'Redmi Note 8 Pro',
                'device_brand': 'Redmi',
                'os_version': '10',
                'os_api': '29',
                'resolution': '1080*2340',
                'dpi': '395'
            },
            {
                'device_type': 'OnePlus 7T',
                'device_brand': 'OnePlus',
                'os_version': '11',
                'os_api': '30',
                'resolution': '1080*2400',
                'dpi': '402'
            }
        ]
        return random.choice(devices)
    
    async def login_account(self, account: TikTokAccount) -> bool:
        """تسجيل دخول الحساب"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay()
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # محاولة تسجيل الدخول عبر API
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
                'aid': '1988'
            }
            
            response = self.session.post(
                f"{TIKTOK_BASE_URL}/passport/web/login/",
                data=login_data,
                timeout=30
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
    
    def extract_video_info(self, video_url: str) -> Tuple[Optional[str], Optional[str]]:
        """استخراج معلومات الفيديو من الرابط"""
        try:
            # تنظيف الرابط
            if '?' in video_url:
                video_url = video_url.split('?')[0]
            
            # استخراج معرف الفيديو
            video_id_match = re.search(r'/video/(\d+)', video_url)
            if not video_id_match:
                return None, None
            
            video_id = video_id_match.group(1)
            
            # استخراج اسم المستخدم
            username_match = re.search(r'@([^/]+)', video_url)
            username = username_match.group(1) if username_match else None
            
            # الحصول على معرف المستخدم
            user_id = None
            if username:
                user_id = self._get_user_id(username)
            
            return video_id, user_id
            
        except Exception as e:
            print(f"خطأ في استخراج معلومات الفيديو: {e}")
            return None, None
    
    def _get_user_id(self, username: str) -> Optional[str]:
        """الحصول على معرف المستخدم"""
        try:
            response = self.session.get(
                f"{TIKTOK_BASE_URL}/@{username}",
                timeout=15
            )
            
            if response.status_code == 200:
                # البحث عن معرف المستخدم في HTML
                user_id_match = re.search(r'"id":"(\d+)"', response.text)
                if user_id_match:
                    return user_id_match.group(1)
                
                # البحث في JSON
                json_match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', response.text)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        # استخراج معرف المستخدم من البيانات
                        user_info = data.get('UserModule', {}).get('users', {}).get(username, {})
                        return user_info.get('id')
                    except Exception:
                        return None
            
            return None
            
        except Exception as e:
            print(f"خطأ في الحصول على معرف المستخدم: {e}")
            return None
    
    async def report_video(self, account: TikTokAccount, video_id: str, user_id: str, reason: int) -> bool:
        """إبلاغ عن فيديو"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay()
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # بناء بيانات البلاغ
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
                'app_name': 'musical_ly',
                'version_code': '370805',
                'version_name': '37.8.5',
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000, 9999)),
                'device_id': str(random.randint(1000, 9999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000))
            }
            
            # إرسال البلاغ
            response = self.session.post(
                f"{TIKTOK_API_BASE}/aweme/v2/aweme/feedback/",
                data=report_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('status_code') == 0
                
                if success:
                    account.mark_success()
                else:
                    account.mark_failure(f"فشل في البلاغ: {result.get('status_msg', 'خطأ غير معروف')}")
                
                return success
            
            account.mark_failure(f"خطأ في الاستجابة: {response.status_code}")
            return False
            
        except Exception as e:
            error_msg = f"خطأ في إبلاغ الفيديو: {e}"
            account.mark_failure(error_msg)
            print(error_msg)
            return False
    
    async def report_account(self, account: TikTokAccount, target_username: str, reason: int) -> bool:
        """إبلاغ عن حساب"""
        try:
            # محاكاة تأخير بشري
            self._simulate_human_delay()
            
            # تحديث User-Agent
            self.session.headers['User-Agent'] = random.choice(self.user_agents)
            
            # الحصول على معرف المستخدم المستهدف
            target_user_id = self._get_user_id(target_username)
            if not target_user_id:
                account.mark_failure("فشل في الحصول على معرف المستخدم المستهدف")
                return False
            
            # معلومات الجهاز
            device_info = self._get_device_info()
            
            # بناء بيانات البلاغ
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
                'app_name': 'musical_ly',
                'version_code': '370805',
                'version_name': '37.8.5',
                'ts': str(int(time.time())),
                'iid': str(random.randint(1000, 9999)),
                'device_id': str(random.randint(1000, 9999)),
                'openudid': str(uuid.uuid4()),
                '_rticket': str(int(time.time() * 1000))
            }
            
            # إرسال البلاغ
            response = self.session.post(
                f"{TIKTOK_API_BASE}/aweme/v2/aweme/feedback/",
                data=report_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('status_code') == 0
                
                if success:
                    account.mark_success()
                else:
                    account.mark_failure(f"فشل في البلاغ: {result.get('status_msg', 'خطأ غير معروف')}")
                
                return success
            
            account.mark_failure(f"خطأ في الاستجابة: {response.status_code}")
            return False
            
        except Exception as e:
            error_msg = f"خطأ في إبلاغ الحساب: {e}"
            account.mark_failure(error_msg)
            print(error_msg)
            return False
    
    def validate_target(self, target: str) -> Tuple[str, Optional[str], Optional[str]]:
        """التحقق من صحة الهدف وتحديد نوعه"""
        target = target.strip()
        
        if '/video/' in target:
            # فيديو
            video_id, user_id = self.extract_video_info(target)
            return 'video', video_id, user_id
        elif target.startswith('@') or '@' in target:
            # حساب
            username = target.replace('@', '').split('/')[0]
            user_id = self._get_user_id(username)
            return 'account', username, user_id
        else:
            # محاولة استخراج كاسم مستخدم
            user_id = self._get_user_id(target)
            if user_id:
                return 'account', target, user_id
        
        return 'unknown', None, None
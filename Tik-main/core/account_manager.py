import json
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.account import TikTokAccount
from utils.encryption import CredentialEncryption

class TikTokAccountManager:
    def __init__(self, storage_file: str = "accounts.json"):
        self.storage_file = storage_file
        self.encryption = CredentialEncryption()
        self.accounts: Dict[str, TikTokAccount] = {}
        self._load_accounts()
    
    def _load_accounts(self):
        """تحميل الحسابات من الملف"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for account_data in data:
                        account = TikTokAccount.from_dict(account_data)
                        self.accounts[account.id] = account
        except Exception as e:
            print(f"خطأ في تحميل الحسابات: {e}")
    
    def _save_accounts(self):
        """حفظ الحسابات إلى الملف"""
        try:
            accounts_data = [account.to_dict() for account in self.accounts.values()]
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(accounts_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطأ في حفظ الحسابات: {e}")
    
    def add_account(self, username: str, password: str, proxy: Optional[str] = None) -> str:
        """إضافة حساب جديد"""
        # فحص عدم وجود الحساب مسبقاً
        for account in self.accounts.values():
            if account.username == username:
                raise ValueError(f"الحساب {username} موجود مسبقاً")
        
        # إنشاء معرف فريد
        account_id = str(uuid.uuid4())
        
        # تشفير كلمة المرور
        encrypted_password = self.encryption.encrypt(password)
        encrypted_cookies = self.encryption.encrypt("")
        
        # إنشاء الحساب
        account = TikTokAccount(
            id=account_id,
            username=username,
            encrypted_password=encrypted_password,
            encrypted_cookies=encrypted_cookies,
            proxy=proxy
        )
        
        self.accounts[account_id] = account
        self._save_accounts()
        
        return account_id
    
    def remove_account(self, account_id: str) -> bool:
        """حذف حساب"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            self._save_accounts()
            return True
        return False
    
    def remove_account_by_username(self, username: str) -> bool:
        """حذف حساب بواسطة اسم المستخدم"""
        for account_id, account in self.accounts.items():
            if account.username == username:
                del self.accounts[account_id]
                self._save_accounts()
                return True
        return False
    
    def get_account(self, account_id: str) -> Optional[TikTokAccount]:
        """الحصول على حساب بواسطة المعرف"""
        return self.accounts.get(account_id)
    
    def get_account_by_username(self, username: str) -> Optional[TikTokAccount]:
        """الحصول على حساب بواسطة اسم المستخدم"""
        for account in self.accounts.values():
            if account.username == username:
                return account
        return None
    
    def get_all_accounts(self) -> List[TikTokAccount]:
        """الحصول على جميع الحسابات"""
        return list(self.accounts.values())
    
    def get_healthy_accounts(self) -> List[TikTokAccount]:
        """الحصول على الحسابات السليمة فقط"""
        return [account for account in self.accounts.values() if account.is_healthy()]
    
    def get_accounts_by_status(self, status: str) -> List[TikTokAccount]:
        """الحصول على الحسابات حسب الحالة"""
        return [account for account in self.accounts.values() if account.status == status]
    
    async def update_account_status(self, account_id: str, status: str, error_message: Optional[str] = None):
        """تحديث حالة الحساب"""
        account = self.accounts.get(account_id)
        if account:
            account.status = status
            if error_message:
                account.last_error = error_message
            account.last_used = datetime.now()
            self._save_accounts()
    
    def quarantine_account(self, account_id: str, reason: str):
        """عزل الحساب"""
        account = self.accounts.get(account_id)
        if account:
            account.quarantine(reason)
            self._save_accounts()
    
    def reactivate_account(self, account_id: str):
        """إعادة تفعيل الحساب"""
        account = self.accounts.get(account_id)
        if account:
            account.status = "active"
            account.fail_count = 0
            account.last_error = None
            self._save_accounts()
    
    def update_account_cookies(self, account_id: str, cookies: str):
        """تحديث كوكيز الحساب"""
        account = self.accounts.get(account_id)
        if account:
            account.encrypted_cookies = self.encryption.encrypt(cookies)
            self._save_accounts()
    
    def get_account_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الحسابات"""
        total_accounts = len(self.accounts)
        active_accounts = len([a for a in self.accounts.values() if a.status == "active"])
        quarantined_accounts = len([a for a in self.accounts.values() if a.status == "quarantined"])
        banned_accounts = len([a for a in self.accounts.values() if a.status == "banned"])
        
        return {
            'total': total_accounts,
            'active': active_accounts,
            'quarantined': quarantined_accounts,
            'banned': banned_accounts
        }
    
    def health_check(self):
        """فحص صحة جميع الحسابات"""
        for account in self.accounts.values():
            if account.status == "active" and account.fail_count >= 5:
                account.status = "quarantined"
        
        self._save_accounts()
    
    def get_decrypted_password(self, account_id: str) -> Optional[str]:
        """الحصول على كلمة المرور المفكوكة"""
        account = self.accounts.get(account_id)
        if account:
            return self.encryption.decrypt(account.encrypted_password)
        return None
    
    def get_decrypted_cookies(self, account_id: str) -> Optional[str]:
        """الحصول على الكوكيز المفكوكة"""
        account = self.accounts.get(account_id)
        if account:
            return self.encryption.decrypt(account.encrypted_cookies)
        return None
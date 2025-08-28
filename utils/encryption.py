from cryptography.fernet import Fernet
import base64
from config.settings import ENCRYPTION_KEY

class CredentialEncryption:
    def __init__(self):
        self.key = self._generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def _generate_key(self):
        """توليد مفتاح التشفير"""
        if len(ENCRYPTION_KEY) >= 32:
            # استخدام المفتاح المحدد في الإعدادات
            key = ENCRYPTION_KEY[:32].encode()
        else:
            # توليد مفتاح جديد
            key = Fernet.generate_key()
        
        return key
    
    def encrypt(self, data: str) -> str:
        """تشفير البيانات"""
        if not data:
            return ""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """فك تشفير البيانات"""
        if not encrypted_data:
            return ""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            return ""
    
    def get_key(self) -> str:
        """الحصول على مفتاح التشفير"""
        return base64.urlsafe_b64encode(self.key).decode()
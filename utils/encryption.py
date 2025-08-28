from cryptography.fernet import Fernet
import base64
from config.settings import ENCRYPTION_KEY

class CredentialEncryption:
    def __init__(self):
        self.key = self._generate_key()
        try:
            self.cipher_suite = Fernet(self.key)
        except Exception:
            # إذا كانت قيمة البيئة غير صالحة، نولّد مفتاحاً جديداً آمنًا
            self.key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.key)
    
    def _generate_key(self):
        """توليد مفتاح التشفير"""
        env_key = ENCRYPTION_KEY or ""
        if env_key:
            # نعتبر أن المفتاح الممرر هو مفتاح Fernet بصيغة base64 urlsafe
            return env_key.encode()
        # توليد مفتاح جديد إذا لم تُحدد قيمة
        return Fernet.generate_key()
    
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
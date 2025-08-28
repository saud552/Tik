from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class TikTokAccount:
    id: str
    username: str
    encrypted_password: str
    encrypted_cookies: str
    status: str = "active"  # active, banned, quarantined, error
    last_used: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime = None
    proxy: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل الحساب إلى قاموس"""
        return {
            'id': self.id,
            'username': self.username,
            'encrypted_password': self.encrypted_password,
            'encrypted_cookies': self.encrypted_cookies,
            'status': self.status,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat(),
            'proxy': self.proxy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TikTokAccount':
        """إنشاء حساب من قاموس"""
        # تحويل التواريخ
        if data.get('last_used'):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
    
    def is_healthy(self) -> bool:
        """فحص صحة الحساب"""
        return self.status == "active" and self.fail_count < 5
    
    def mark_success(self):
        """تسجيل نجاح العملية"""
        self.success_count += 1
        self.last_used = datetime.now()
        self.last_error = None
    
    def mark_failure(self, error: str):
        """تسجيل فشل العملية"""
        self.fail_count += 1
        self.last_error = error
        self.last_used = datetime.now()
        
        if self.fail_count >= 5:
            self.status = "quarantined"
    
    def quarantine(self, reason: str):
        """عزل الحساب"""
        self.status = "quarantined"
        self.last_error = reason
        self.last_used = datetime.now()
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class ReportType(Enum):
    VIDEO = "video"
    ACCOUNT = "account"

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ReportJob:
    report_type: ReportType
    target: str  # رابط الفيديو أو اسم المستخدم
    reason: int  # نوع البلاغ
    reports_per_account: int
    id: str = None
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_reports: int = 0
    successful_reports: int = 0
    failed_reports: int = 0
    assigned_accounts: List[str] = None
    progress: Dict[str, Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.assigned_accounts is None:
            self.assigned_accounts = []
        if self.progress is None:
            self.progress = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل المهمة إلى قاموس"""
        return {
            'id': self.id,
            'report_type': self.report_type.value,
            'target': self.target,
            'reason': self.reason,
            'reports_per_account': self.reports_per_account,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_reports': self.total_reports,
            'successful_reports': self.successful_reports,
            'failed_reports': self.failed_reports,
            'assigned_accounts': self.assigned_accounts,
            'progress': self.progress,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportJob':
        """إنشاء مهمة من قاموس"""
        # تحويل التواريخ
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        # تحويل Enum
        data['report_type'] = ReportType(data['report_type'])
        data['status'] = JobStatus(data['status'])
        
        return cls(**data)
    
    def start(self):
        """بدء المهمة"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
    
    def complete(self):
        """إكمال المهمة"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def fail(self, error: str):
        """فشل المهمة"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error
    
    def cancel(self):
        """إلغاء المهمة"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def update_progress(self, account_id: str, status: str, message: str = ""):
        """تحديث تقدم المهمة"""
        self.progress[account_id] = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_progress_percentage(self) -> float:
        """الحصول على نسبة التقدم"""
        if self.total_reports == 0:
            return 0.0
        return (self.successful_reports + self.failed_reports) / self.total_reports * 100
import asyncio
import random
from typing import List, Dict, Any, Optional
from models.job import ReportJob, ReportType, JobStatus
from models.account import TikTokAccount
from core.tiktok_reporter import TikTokReporter
from core.account_manager import TikTokAccountManager
from config.settings import HUMAN_DELAYS

class ReportScheduler:
    def __init__(self, account_manager: TikTokAccountManager):
        self.account_manager = account_manager
        self.reporter = TikTokReporter(account_manager)
        self.active_jobs: Dict[str, ReportJob] = {}
        self.job_queue: List[ReportJob] = []
        self.is_running = False
        self.stop_event = asyncio.Event()
    
    async def queue_job(self, report_type: ReportType, target: str, reason: int, 
                        reports_per_account: int, socks5_proxies: Optional[list[str]] = None) -> str:
        """إضافة مهمة جديدة إلى الطابور"""
        # إنشاء مهمة جديدة
        job = ReportJob(
            report_type=report_type,
            target=target,
            reason=reason,
            reports_per_account=reports_per_account
        )
        
        # حساب إجمالي البلاغات المطلوبة
        healthy_accounts = self.account_manager.get_healthy_accounts()
        if not healthy_accounts:
            raise ValueError("لا توجد حسابات سليمة متاحة")
        
        total_reports = len(healthy_accounts) * reports_per_account
        job.total_reports = total_reports
        
        # إضافة المهمة إلى الطابور
        # حفظ البروكسيات المفعلة في progress للشفافية (اختياري)
        if socks5_proxies:
            job.progress['proxies'] = socks5_proxies
        self.job_queue.append(job)
        
        # بدء المعالجة إذا لم تكن تعمل
        if not self.is_running:
            asyncio.create_task(self.process_job_queue())
        
        return job.id
    
    async def process_job_queue(self):
        """معالجة طابور المهام"""
        self.is_running = True
        
        while self.job_queue and not self.stop_event.is_set():
            job = self.job_queue.pop(0)
            await self.execute_job(job)
        
        self.is_running = False
    
    async def execute_job(self, job: ReportJob):
        """تنفيذ مهمة البلاغ"""
        try:
            # بدء المهمة
            job.start()
            self.active_jobs[job.id] = job
            
            # الحصول على الحسابات السليمة
            healthy_accounts = self.account_manager.get_healthy_accounts()
            if not healthy_accounts:
                job.fail("لا توجد حسابات سليمة متاحة")
                return
            
            # توزيع البلاغات على الحسابات
            await self.distribute_reports(job, healthy_accounts)
            
            # إكمال المهمة
            if job.successful_reports > 0:
                job.complete()
            else:
                job.fail("لم يتم إرسال أي بلاغ بنجاح")
                
        except Exception as e:
            job.fail(f"خطأ في تنفيذ المهمة: {e}")
        finally:
            # إزالة المهمة من المهام النشطة
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
    
    async def distribute_reports(self, job: ReportJob, accounts: List[TikTokAccount]):
        """توزيع البلاغات على الحسابات"""
        # توزيع البلاغات بالتساوي
        reports_per_account = job.reports_per_account
        proxies_list = job.progress.get('proxies') if isinstance(job.progress, dict) else None
        proxy_index = 0
        
        for account in accounts:
            if self.stop_event.is_set():
                break
                
            # إعداد بروكسي socks5 إن وجد
            if proxies_list:
                if proxy_index >= len(proxies_list):
                    proxy_index = 0
                socks = proxies_list[proxy_index]
                proxy_index += 1
                self.reporter.session.proxies.update({'http': socks, 'https': socks})
            else:
                # إزالة أي بروكسي سابق
                self.reporter.session.proxies.pop('http', None)
                self.reporter.session.proxies.pop('https', None)

            # تسجيل الدخول إلى الحساب
            if not await self.reporter.login_account(account):
                job.update_progress(account.id, "failed", "فشل في تسجيل الدخول")
                continue
            
            # تنفيذ البلاغات من هذا الحساب
            for i in range(reports_per_account):
                if self.stop_event.is_set():
                    break
                
                success = False
                if job.report_type == ReportType.VIDEO:
                    # استخراج معلومات الفيديو
                    video_info = await self.reporter.extract_video_info(job.target)
                    if not video_info or not video_info[0] or not video_info[1]:
                        job.update_progress(account.id, "failed", "فشل في استخراج معلومات الفيديو")
                        continue
                    
                    video_id, owner_user_id = video_info
                    success = await self.reporter.report_video(account, video_id, owner_user_id, job.reason)
                elif job.report_type == ReportType.ACCOUNT:
                    success = await self.reporter.report_account(
                        account, job.target, job.reason
                    )
                
                if success:
                    job.successful_reports += 1
                    job.update_progress(account.id, "success", f"بلاغ {i+1} تم بنجاح")
                else:
                    job.failed_reports += 1
                    job.update_progress(account.id, "failed", f"بلاغ {i+1} فشل")
                
                # تأخير بين البلاغات
                if i < reports_per_account - 1:
                    await asyncio.sleep(random.uniform(
                        HUMAN_DELAYS['min_delay'], 
                        HUMAN_DELAYS['max_delay']
                    ))
            
            # تحديث حالة الحساب
            self.account_manager._save_accounts()
    
    async def stop_job(self, job_id: str) -> bool:
        """إيقاف مهمة محددة"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.cancel()
            del self.active_jobs[job_id]
            return True
        return False
    
    async def stop_all_jobs(self):
        """إيقاف جميع المهام"""
        self.stop_event.set()
        
        # إيقاف المهام النشطة
        for job in self.active_jobs.values():
            job.cancel()
        
        # إفراغ الطابور
        self.job_queue.clear()
        self.active_jobs.clear()
        
        # إعادة تعيين حدث الإيقاف
        self.stop_event.clear()
    
    def get_job_status(self, job_id: str) -> Optional[ReportJob]:
        """الحصول على حالة مهمة محددة"""
        # البحث في المهام النشطة
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # البحث في الطابور
        for job in self.job_queue:
            if job.id == job_id:
                return job
        
        return None
    
    def get_all_jobs(self) -> List[ReportJob]:
        """الحصول على جميع المهام"""
        all_jobs: List[ReportJob] = []
        
        # المهام النشطة
        all_jobs.extend(self.active_jobs.values())
        
        # المهام في الطابور
        all_jobs.extend(self.job_queue)
        
        return all_jobs
    
    def get_job_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المهام"""
        active_jobs = len(self.active_jobs)
        queued_jobs = len(self.job_queue)
        total_jobs = active_jobs + queued_jobs
        
        # إحصائيات إضافية
        total_reports = 0
        successful_reports = 0
        failed_reports = 0
        
        for job in self.active_jobs.values():
            total_reports += job.total_reports
            successful_reports += job.successful_reports
            failed_reports += job.failed_reports
        
        return {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'queued_jobs': queued_jobs,
            'total_reports': total_reports,
            'successful_reports': successful_reports,
            'failed_reports': failed_reports
        }
    
    async def retry_failed_reports(self, job_id: str) -> bool:
        """إعادة محاولة البلاغات الفاشلة"""
        job = self.get_job_status(job_id)
        if not job or job.status != JobStatus.FAILED:
            return False
        
        # إعادة تعيين المهمة
        job.status = JobStatus.PENDING
        job.failed_reports = 0
        job.successful_reports = 0
        job.progress.clear()
        
        # إضافة المهمة إلى الطابور مرة أخرى
        self.job_queue.append(job)
        
        # بدء المعالجة إذا لم تكن تعمل
        if not self.is_running:
            asyncio.create_task(self.process_job_queue())
        
        return True
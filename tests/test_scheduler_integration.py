import asyncio
from typing import Tuple

from core.report_scheduler import ReportScheduler
from core.account_manager import TikTokAccountManager
from models.account import TikTokAccount
from models.job import ReportType


def test_scheduler_executes_video_reports_with_patched_network(tmp_path):
    storage_file = tmp_path / "accounts.json"
    manager = TikTokAccountManager(str(storage_file))

    account_id = manager.add_account("user1", "pass1")
    account = manager.get_account(account_id)
    assert account is not None

    scheduler = ReportScheduler(manager)

    async def fake_login_account(acct: TikTokAccount) -> bool:
        return True

    def fake_extract_video_info(url: str) -> Tuple[str, str]:
        return ("123456", "9999")

    async def fake_report_video(acct: TikTokAccount, vid: str, uid: str, reason: int) -> bool:
        assert vid == "123456" and uid == "9999" and reason == 1
        return True

    scheduler.reporter.login_account = fake_login_account  # type: ignore
    scheduler.reporter.extract_video_info = fake_extract_video_info  # type: ignore
    scheduler.reporter.report_video = fake_report_video  # type: ignore

    async def run_flow():
        job_id_local = await scheduler.queue_job(ReportType.VIDEO, "https://tiktok.com/@u/video/1", 1, 2)
        # wait until queue finishes
        while scheduler.is_running:
            await asyncio.sleep(0.01)
        return job_id_local

    job_id = asyncio.run(run_flow())
    job = scheduler.get_job_status(job_id)
    assert job is None


def test_scheduler_executes_account_reports_with_patched_network(tmp_path):
    storage_file = tmp_path / "accounts.json"
    manager = TikTokAccountManager(str(storage_file))

    account_id = manager.add_account("user1", "pass1")
    assert manager.get_account(account_id) is not None

    scheduler = ReportScheduler(manager)

    async def fake_login_account(acct: TikTokAccount) -> bool:
        return True

    async def fake_report_account(acct: TikTokAccount, username: str, reason: int) -> bool:
        assert username == "target_user" and reason == 2
        return True

    scheduler.reporter.login_account = fake_login_account  # type: ignore
    scheduler.reporter.report_account = fake_report_account  # type: ignore

    async def run_flow():
        job_id_local = await scheduler.queue_job(ReportType.ACCOUNT, "target_user", 2, 1)
        while scheduler.is_running:
            await asyncio.sleep(0.01)
        return job_id_local

    job_id = asyncio.run(run_flow())
    job = scheduler.get_job_status(job_id)
    assert job is None


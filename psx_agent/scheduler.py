from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from psx_agent.config import get_settings
from psx_agent.jobs.preopen_report import main as write_preopen_report


def main() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.report_timezone)
    scheduler.add_job(
        write_preopen_report,
        CronTrigger(day_of_week="mon-fri", hour=8, minute=45),
        id="psx_preopen_report",
        replace_existing=True,
    )
    print(f"Scheduler started. Pre-open report runs at 08:45 {settings.report_timezone}, Monday-Friday.")
    scheduler.start()


if __name__ == "__main__":
    main()

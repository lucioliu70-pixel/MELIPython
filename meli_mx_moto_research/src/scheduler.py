from __future__ import annotations

import schedule
import time


def run_daily(job_func, at: str = "09:00"):
    schedule.every().day.at(at).do(job_func)
    while True:
        schedule.run_pending()
        time.sleep(1)

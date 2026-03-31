from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class CronJob:
    job_id: str
    every_seconds: int
    message: str


class CronManager:
    def __init__(self) -> None:
        self._jobs: dict[str, CronJob] = {}

    def add_job(self, job_id: str, every_seconds: int, message: str) -> CronJob:
        if every_seconds <= 0:
            raise ValueError("every_seconds must be > 0")
        job = CronJob(job_id=job_id, every_seconds=every_seconds, message=message)
        self._jobs[job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def list_jobs(self) -> list[dict]:
        return [asdict(job) for job in self._jobs.values()]

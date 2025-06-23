import asyncio
from typing import List
from aiojobs import Job, Scheduler
from setezor.tasks.base_job import BaseJob
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.tasks.nmap_parse_task import NmapParseTask
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.scapy_scan_task import ScapySniffTask
from setezor.tasks.wappalyzer_logs_task import WappalyzerLogsTask
from setezor.tasks.snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from setezor.interfaces.observer import Observable, Observer
from setezor.unit_of_work.unit_of_work import UnitOfWork


class CustomScheduler(Scheduler):
    def __init__(self, *args, **kwrags):
        super().__init__(*args, **kwrags)

    async def spawn_job(self, job: BaseJob) -> Job:
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        should_start = self._limit is None or self.active_count < self._limit
        if should_start:
            job._start()
        else:
            try:
                await self._pending.put(job)
            except asyncio.CancelledError:
                await job.close()
                raise
        self._jobs.add(job)
        return job

    @property
    def jobs(self):
        return self._jobs


class SchedulerManager:
    settings = {
        NmapScanTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        NmapParseTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 5,
            "pending_limit": 10000
        },
        MasscanScanTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        ScapySniffTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        WappalyzerLogsTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 5,
            "pending_limit": 10000
        },
        SnmpBruteCommunityStringTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        }
    }

    @classmethod
    def for_job(cls, job: BaseJob):
        if job in cls.settings:
            return CustomScheduler(**cls.settings[job])
        return CustomScheduler()

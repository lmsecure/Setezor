from setezor.tasks.base_job import BaseJob
from setezor.restructors.speed_test_task_restructor import SpeedTestClientTaskRestructor, SpeedTestServerTaskRestructor


class SpeedTestClientTask(BaseJob):
    restructor = SpeedTestClientTaskRestructor


class SpeedTestServerTask(BaseJob):
    restructor = SpeedTestServerTaskRestructor

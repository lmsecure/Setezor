from .structure import SchedulersParams
from tasks.base_job import CustomScheduler


class Schedulers:
    def __init__(self, params: SchedulersParams):
        self.schedulers = {}
        for name, value in params.__dict__.items():
            self.schedulers.update({name: CustomScheduler(exception_handler=None, **value)})  # FixMe set custom exception handler
            
    def get(self, name: str) -> CustomScheduler:
        return self.schedulers.get(name)
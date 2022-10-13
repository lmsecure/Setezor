from threading import Timer
import weakref


class RepeatTimer(Timer):
    instances = []
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__.instances.append(weakref.proxy(self))
        self.name = name
        
    def run(self):  
        while not self.finished.wait(self.interval):  
            self.function(*self.args,**self.kwargs)  
    
    @classmethod
    def cancel_timer_by_name(cls, name: str):
        for timer in cls.instances:
            if timer.name == name or name == 'all':
                timer.cancel()
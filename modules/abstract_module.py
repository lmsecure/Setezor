from abc import ABC, abstractmethod


class AbstractModule(ABC):
    """Базовый интерфейс для модулей
    """    
    
    @abstractmethod
    async def execute_async(self, *args, **kwargs):
        """Асинхронное выполнение модуля
        """        
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs):
        """Синхронное выполнение модуля
        """        
        pass
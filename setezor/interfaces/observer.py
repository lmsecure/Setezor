from abc import ABC, abstractmethod


class Observable(ABC):
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    @abstractmethod
    def attach(self, observer: "Observer") -> None:
        """
        Attach an observer to the subject.
        """
        pass

    @abstractmethod
    def detach(self, observer: "Observer") -> None:
        """
        Detach an observer from the subject.
        """
        pass

    @abstractmethod
    async def notify(self) -> None:
        """
        Notify all observers about an event.
        """
        pass

class Observer(ABC):
    """
    The Observer interface declares the update method, used by subjects.
    """

    @abstractmethod
    async def notify(self, subject: Observable) -> None:
        """
        Receive update from subject.
        """
        pass
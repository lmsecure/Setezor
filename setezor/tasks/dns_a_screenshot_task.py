from setezor.tasks.base_job import BaseJob
from setezor.restructors.dns_a_screenshot_restructor import DNSAScreenshotTaskRestructor


class DNS_A_ScreenshotTask(BaseJob):
    """
    Серверная таска для обработки результатов DNS A Screenshot от агента.
    Эта таска не выполняет никакой работы на сервере, а только обрабатывает
    результаты, полученные от агента через реструктор.
    """

    logs_folder = "screenshots"
    restructor = DNSAScreenshotTaskRestructor

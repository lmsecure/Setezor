from setezor.modules.speed_test.speed_test import SpeedTest

class SpeedTestClientTaskRestructor:
    @classmethod
    async def restruct(cls, *args, **kwargs) -> list:
        return []


class SpeedTestServerTaskRestructor:
    @classmethod
    async def restruct(cls, ip_id_from: str, ip_id_to: str, speed: float, port: int, protocol: str) -> list:
        result = SpeedTest.restruct_result(ip_id_from=ip_id_from, ip_id_to=ip_id_to, speed=speed, port=port, protocol=protocol)
        return result
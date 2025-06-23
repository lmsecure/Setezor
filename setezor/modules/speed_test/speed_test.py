from setezor.models.network_speed_test import NetworkSpeedTest



class SpeedTest:

    @classmethod
    def restruct_result(cls, ip_id_from: str, ip_id_to: str, speed: float, port: int, protocol: str) -> list:
        return [NetworkSpeedTest(ip_id_from=ip_id_from, ip_id_to=ip_id_to, speed=speed, port=port, protocol=protocol)]

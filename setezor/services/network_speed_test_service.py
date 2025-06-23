from setezor.services.base_service import BaseService


class NetworkSpeedTestService(BaseService):
    async def get_result(self, project_id: str, ip_id_from: str, ip_id_to: str) -> list:
        async with self._uow:
            objs = await self._uow.network_speed_test.filter(project_id=project_id, ip_id_from=ip_id_from, ip_id_to=ip_id_to)
        result = []
        for obj in objs:
            result.append(
                {
                    "speed": obj.speed,
                    "port": obj.port,
                    "protocol": obj.protocol
                }
            )
        return result

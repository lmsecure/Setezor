from setezor.services.base_service import BaseService
from setezor.models import NetworkSpeedTest

from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.services.task_result_services.base_task_service import BaseTaskService



class SpeedTestResolveObjects(BaseTaskService):
    def __init__(self, uow: UnitOfWork, agent_id: str, project_id: str, scan_id: str,
                 ip_id_from: str, ip_id_to: str, speed: float, port: int, protocol: str):
        super().__init__(uow = uow)

        self.project_id = project_id
        self.scan_id = scan_id
        self.agent_id = agent_id

        self.data = {
            "project_id": project_id,
            "scan_id": scan_id,
            "ip_id_from": ip_id_from,
            "ip_id_to": ip_id_to,
            "port": port,
            "protocol": protocol
        }
        self.speed = speed


    async def _get_or_create_network_speed_test(self):
        network_speed_test_obj = await self.uow.network_speed_test.find_one(with_deleted_at=False, **self.data)
        if network_speed_test_obj:
            await self.uow.network_speed_test.edit_one(
                id = network_speed_test_obj.id,
                data = self.data | {"speed": self.speed}
            )
            return network_speed_test_obj
        network_speed_test_obj: NetworkSpeedTest = self.uow.network_speed_test.add(data=self.data | {"speed": self.speed})
        return network_speed_test_obj


    async def write_all_to_db(self):
        network_speed_test_obj = await self._get_or_create_network_speed_test()
        return network_speed_test_obj


class SpeedTestTaskService(BaseService):
    async def write_result(self, project_id: str, scan_id: str, agent_id: str,
                           ip_id_from: str, ip_id_to: str, speed: float, port: int, protocol: str) -> None:
        async with self._uow:
            resolver = SpeedTestResolveObjects(
                uow=self._uow,
                project_id=project_id,
                scan_id=scan_id,
                agent_id=agent_id,
                ip_id_from=ip_id_from,
                ip_id_to=ip_id_to,
                speed=speed,
                port=port,
                protocol=protocol
            )
            await resolver.write_all_to_db()
            await self._uow.commit()

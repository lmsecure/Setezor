import json

from setezor.signals.base_signal import Signal


class InformationSignal(Signal):

    async def __call__(self, data: dict, agent_id: str, **kwargs):
        await self.agent_service.set_info(id=agent_id, info=json.dumps(data))
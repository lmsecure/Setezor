from typing import List
from setezor.models.domain import Domain


class Sd_Scan_Task_Restructor:
    @classmethod
    async def restruct(cls, raw_result):
        result: List[Domain] = []
        for domain in raw_result:
            result.append(Domain(domain=domain))
        return result
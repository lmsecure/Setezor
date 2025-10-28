from .base_job import BaseJob
from setezor.models.target import Target
from setezor.restructors.masscan_scan_task_restructor import MasscanTaskRestructor


class MasscanScanTask(BaseJob):
    logs_folder = "masscan_logs"
    restructor = MasscanTaskRestructor

    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        masscan_targets = dict()
        for target in targets:
            if not target.ip:
                continue
            if not (target.ip in masscan_targets):
                masscan_targets[target.ip] = []
            if target.port:
                masscan_targets[target.ip].append(target.port)
        for ip, ports in masscan_targets.items():
            if ports:  # если в скоупе указаны порты для таргета, то он их и подставит
                result_params.append({**base_kwargs} | {"target": ip,
                                                        "ports": ",".join(map(str, ports))})
                continue
            result_params.append({**base_kwargs} | {"target": ip})
        return result_params

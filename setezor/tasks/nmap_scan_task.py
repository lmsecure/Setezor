from setezor.tasks.base_job import BaseJob
from setezor.models.target import Target


class NmapScanTask(BaseJob):

    @classmethod
    def generate_params_from_scope(cls, targets: list[Target], **base_kwargs):
        result_params = []
        nmap_targets = dict()
        for target in targets:
            if not target.ip:
                continue
            if not (target.ip in nmap_targets):
                nmap_targets[target.ip] = []
            if target.port:
                nmap_targets[target.ip].append(target.port)
        for ip, ports in nmap_targets.items():
            if ports:  # если в скоупе указаны порты для таргета, то он их и подставит
                result_params.append({**base_kwargs} | {"targetIP": ip,
                                                        "targetPorts": "-p " + ",".join(map(str, ports))})
                continue
            result_params.append({**base_kwargs} | {"targetIP": ip})
        return result_params
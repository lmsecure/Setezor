import traceback
from time import time
from setezor.tasks.base_job import BaseJob
from setezor.modules.nmap.scanner import NmapScanner
from setezor.modules.nmap.parser import NmapParser
from setezor.tools.ip_tools import get_ipv4, get_mac



class NmapScanTask(BaseJob):
    
    JOB_URL = "nmap_scan_task"

    def __init__ (self, scheduler, name: str, task_id: int, project_id: str,
                        targetIP: str,
                        agent_id: int,
                        interface_ip_id: int,
                        interface: str,
                        targetPorts: str,
                        traceroute: bool,
                        serviceVersion: bool,
                        stealthScan: bool,
                        skipDiscovery: bool,
                        scanTechniques: str = '',
                        portsDiscovery: str = '',
                        requestDiscovery: str = ''):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.interface_ip_id = interface_ip_id
        self.interface = interface
        self.ip = get_ipv4(self.interface)
        self.mac = get_mac(self.interface)
        self.extra_args = [targetIP, targetPorts]
        if traceroute: self.extra_args.append("--traceroute")
        if serviceVersion: self.extra_args.append("-sV")
        if stealthScan: self.extra_args.append("-O")
        if skipDiscovery: self.extra_args.append("-Pn")
        if scanTechniques: self.extra_args.append(scanTechniques)
        if portsDiscovery: self.extra_args.append(portsDiscovery)
        if requestDiscovery: self.extra_args.append(requestDiscovery)
        self.extra_args.append("-e " + interface)
        # self.extra_args.append("-d4")
        self._coro = self.run()


    async def _task_func(self):
        scan_result = await NmapScanner().async_run(extra_args=' '.join(self.extra_args), _password=None)
        parse_result = NmapParser().parse_hosts(scan = scan_result.get('nmaprun'), agent_id=self.agent_id, self_address={'ip': self.ip, 'mac': self.mac})
        return parse_result


    async def run(self):
        try:
            t1 = time()
            data = await self._task_func()
            print(f'Task func "{self.__class__.__name__}" finished after {time() - t1:.2f} seconds')
            result = NmapParser.restruct_result(data=data, interface_ip_id=self.interface_ip_id)
            await self.send_result_to_parent_agent(result=result)
            return result
        except Exception as e:
            print('Task "%s" failed with error\n%s', self.__class__.__name__, traceback.format_exc())
            raise e
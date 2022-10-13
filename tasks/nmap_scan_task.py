from tasks.base_task import BaseTask
from modules.nmap.scanner import NmapScanner
from modules.nmap.parser import NmapParser
from tools.ip_tools import get_self_ip
from database.queries import Queries


class NmapScanTask(BaseTask):
    
    async def _task_func(self, command: str, iface: str, nmap_logs:str, **kwargs):
        """Запускает активное сканирование с использованием nmap-а

        Args:
            command (str): параметры сканирования
            _password (str): пароль супер пользователя для некоторых параметров

        Returns:
            _type_: результат сканирования
        """
        scan_result = await NmapScanner().async_run(extra_args=' '.join(command.split(' ')[3:]), _password=None, logs_path=nmap_logs)
        return NmapParser().parse_hosts(scan=scan_result.get('nmaprun'), self_address=get_self_ip(iface))
    
    def _write_result_to_db(self, db: Queries, result: list, **kwargs):
        """Метод парсинга результатов сканирования nmap-а и занесения в базу

        Args:
            db (Queries): объект запросов в базу
            result (list): результат скаинрования nmap-а
            iface (str): имя сетевого интерфейса
        """
        db.ip.write_many(data=result.addresses)
        db.l3link.write_many(data=result.traces)
        db.port.write_many(data=result.ports)
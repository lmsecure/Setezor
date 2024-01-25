import pandas as pd
import io
from exceptions.loggers import get_logger
import traceback


class XLSXReport:
    def __init__(self) -> None:
        self.logger = get_logger(self.__module__, handlers=[])
    
    def _generate_ips_sheet(self, data: list, writer):
        try:
            self.logger.debug('Start generate IPs sheet to report')
            ports = data.get('port')
            ips = data.get('ip')
            df_ports = pd.DataFrame(ports)
            df_ips = pd.DataFrame(ips)
            df = pd.merge(left=df_ports, right=df_ips, how='inner', left_on=['ip'], right_on=['id'], suffixes=('_x', ''))
            df.fillna('')
            df = df[['ip', 'os_type', 'port', 'protocol', 'state', 'service_name', 'product', 'version', 'extra_info']]
            df.to_excel(writer, sheet_name='IPs')
            self.logger.debug('Finish generate IPs sheet')
        except:
            self.logger.error('Failed to generate IPs sheet with error\n%s', traceback.format_exc())
        
    def _generate_domains_sheet(self, data: list):
        try:
            self.logger.debug('Start generate domains sheet to report')
            self.logger.debug('Finish generate domains sheet')
            pass
        except:
            self.logger.error('Failed to generate IPs sheet with error\n%s', traceback.format_exc())
    
    def _generate_cve_sheet(self, data: list):
        try:
            self.logger.debug('Start generate CVEs sheet to report')
            self.logger.debug('Finish generate CVEs sheet')
            pass
        except:
            self.logger.error('Failed to generate IPs sheet with error\n%s', traceback.format_exc())
    
    def _generate_api_sheet(self, data: list):
        try:
            self.logger.debug('Start generate APIs sheet to report')
            self.logger.debug('Finish generate APIs sheet')
            pass
        except:
            self.logger.error('Failed to generate IPs sheet with error\n%s', traceback.format_exc())
        
    def generate_report(self, tables: dict):
        report = io.BytesIO()
        with pd.ExcelWriter(report, engine='openpyxl') as writer:
            self._generate_ips_sheet(tables, writer)
            # self._generate_domains_sheet(tables.get('domains'))
            # self._generate_cve_sheet(tables.get('cve'))
            # self._generate_api_sheet(tables.get('api'))
        return report
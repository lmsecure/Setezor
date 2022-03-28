from subprocess import Popen, PIPE
import xmltodict
import json
from datetime import datetime
try:
    from config import NmapConfig
except:
    from collections import namedtuple
    NmapConfig = namedtuple('NmapConfig', ['default_ports', 'default_source_path'])('', '')
from exceptions.snanners_exceptions import (
    NmapCommandError,
    NmapParserError,
    NmapSaverError
)
from exceptions.exception_logger import exception_decorator
from exceptions.loggers import LoggerNames, get_logger


class NmapScanner:

    start_command = ['nmap', '-oX', '-']
    scan_type = {'quick': ['-sn'],
                 'quick_traceroute': ['-sn', '--traceroute'],
                 'sw_version': ['-sV'],
                 'scripts': ['-sC'],
                 'stealth_scan': ['-sS'],
                 'custom_scripts': ['--script smb-vuln*'],
                 'ids_bypass_d': ['-D'],
                 'ids_bypass_f': ['-f'],
                 'ids_bypass_y': ['-y'],
                 'ports': ['-p', NmapConfig.default_ports if NmapConfig.default_ports else '']}

    def __init__(self):
        self.logger = get_logger(LoggerNames.scan)

    @exception_decorator(LoggerNames.scan, {})
    def run_scan(self, extra_args: list):
        self.logger.info(f'Start nmap scan with command "{" ".join(self.start_command + extra_args)}"')
        result, error = Popen(self.start_command + extra_args, stdout=PIPE, stderr=PIPE).communicate()
        self.logger.info('Finish nmap scan')
        if error:
            raise NmapCommandError(error.decode())
        parsed = self.parse_xml(result.decode())
        if NmapConfig.default_source_path:
            self.save_source_data(NmapConfig.default_source_path)
        return parsed

    @exception_decorator(LoggerNames.scan, {})
    def parse_xml(self, input_xml: str):
        try:
            dict_xml = xmltodict.parse(input_xml)
            json_result = json.dumps(dict_xml).replace('@', '')
            return json.loads(json_result)
        except:
            raise NmapParserError()

    @exception_decorator(LoggerNames.scan, {})
    def universal_scan(self, target: str, scan_type: str):
        target = target if isinstance(target, list) else target.split(' ')
        extra_params = self.scan_type.get(scan_type)
        if extra_params:
            result = self.run_scan(target + extra_params)
            return result
        else:
            raise NmapCommandError(f'Could not find type "{scan_type}"')

    def interactive_scan(self, extra_args: str):
        result = self.run_scan(extra_args.replace(';', '').split(' '))
        return result

    @exception_decorator(LoggerNames.scan, False)
    def save_source_data(self, path: str, scan_xml: bytes, command: str):
        full_path = f'{path}/{datetime.now()}{command}.xml'
        self.logger.info(f'Save scan_data to file by path "{full_path}"')
        try:
            with open(full_path, 'wb') as f:
                f.write(scan_xml)
            return True
        except:
            raise NmapSaverError(full_path)

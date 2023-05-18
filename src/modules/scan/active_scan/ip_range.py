import iptools
from exceptions.exception_logger import exception_decorator
from exceptions.loggers import LoggerNames


class IPv4Range:
    
    
    @exception_decorator(LoggerNames.scan, [])
    def split_range(source_range: str):
        if not IPv4Range.validate_range(source_range):
            raise Exception(f'Invalide IPv4 address "{source_range}"')  # FixMe add custom exception
        if '-' in source_range:
            return IPv4Range.to_list_by_dash(source_range)
        elif '/' in source_range:
            return IPv4Range.to_list_by_netmask(source_range)
        else:
            return [source_range]
        
    @staticmethod
    def to_list_by_netmask(ip_range: str):
        return list(iptools.IpRange(ip_range))
    
    @staticmethod
    def to_list_by_dash(ip_range: str):
        octeds = [i.split('-') if '-' in i else i for i in ip_range.split('.')]
        octeds_range = [map(str, range(*[int(j) + 1 if index == len(i) - 1 else int(j) for index, j in enumerate(i)])) if isinstance(i, list) else [i] for i in octeds]
        addresses = ['']
        for octed in octeds_range:
            tmp_addr = [f'{j}.{i}' if j else i for i in octed  for j in addresses]
            addresses = tmp_addr
        return addresses

    @staticmethod
    def validate_range(ip_range: str):
        is_valid_netmask =  0 < int(ip_range.split('/')[1]) < 33 if '/' in ip_range else True
        is_valid_octeds = all([0 <= int(i) < 255 if '-' not in i else all([0 <= int(j)< 255 for j in i.split('-')]) 
                               for i in ip_range.split('/')[0].split('.')])
        return all([is_valid_netmask, is_valid_octeds])
            
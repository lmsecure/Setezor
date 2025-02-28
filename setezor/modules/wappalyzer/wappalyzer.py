import re

from setezor.models import IP, Port, Domain, Software, Vendor, L7, L7Software
from setezor.network_structures import SoftwareStruct
# from setezor.modules.osint.dns_info.dns_info import DNS
from setezor.modules.osint.dns_info.dns_info import DNS as DNSModule
from ipaddress import IPv4Address

from cpeguess.cpeguess import CPEGuess


class WappalyzerParser:

    categories = {1: 'CMS', 2: 'Message boards', 3: 'Database managers',
                  4: 'Documentation', 5: 'Widgets', 6: 'Ecommerce',
                  7: 'Photo galleries', 8: 'Wikis', 9: 'Hosting panels',
                  10: 'Analytics', 11: 'Blogs', 12: 'JavaScript frameworks',
                  13: 'Issue trackers', 14: 'Video players', 15: 'Comment systems',
                  16: 'Security', 17: 'Font scripts', 18: 'Web frameworks',
                  19: 'Miscellaneous', 20: 'Editors', 21: 'LMS', 22: 'Web servers',
                  23: 'Caching', 24: 'Rich text editors', 25: 'JavaScript graphics',
                  26: 'Mobile frameworks', 27: 'Programming languages', 28: 'Operating systems',
                  29: 'Search engines', 30: 'Webmail', 31: 'CDN', 32: 'Marketing automation',
                  33: 'Web server extensions', 34: 'Databases', 35: 'Maps',
                  36: 'Advertising', 37: 'Network devices', 38: 'Media servers',
                  39: 'Webcams', 41: 'Payment processors', 42: 'Tag managers',
                  44: 'CI', 45: 'Control systems', 46: 'Remote access', 47: 'Development',
                  48: 'Network storage', 49: 'Feed readers', 50: 'DMS',
                  51: 'Page builders', 52: 'Live chat', 53: 'CRM', 54: 'SEO',
                  55: 'Accounting', 56: 'Cryptominers', 57: 'Static site generator',
                  58: 'User onboarding', 59: 'JavaScript libraries', 60: 'Containers',
                  62: 'PaaS', 63: 'IaaS', 64: 'Reverse proxies', 65: 'Load balancers',
                  66: 'UI frameworks', 67: 'Cookie compliance', 68: 'Accessibility',
                  69: 'Authentication', 70: 'SSL/TLS certificate authorities', 71: 'Affiliate programs',
                  72: 'Appointment scheduling', 73: 'Surveys', 74: 'A/B Testing', 75: 'Email',
                  76: 'Personalisation', 77: 'Retargeting', 78: 'RUM', 79: 'Geolocation',
                  80: 'WordPress themes', 81: 'Shopify themes', 82: 'Drupal themes',
                  83: 'Browser fingerprinting', 84: 'Loyalty & rewards', 85: 'Feature management',
                  86: 'Segmentation', 87: 'WordPress plugins', 88: 'Hosting', 89: 'Translation',
                  90: 'Reviews', 91: 'Buy now pay later', 92: 'Performance', 93: 'Reservations & delivery',
                  94: 'Referral marketing', 95: 'Digital asset management', 96: 'Content curation',
                  97: 'Customer data platform', 98: 'Cart abandonment', 99: 'Shipping carriers',
                  100: 'Shopify apps', 101: 'Recruitment & staffing', 102: 'Returns', 103: 'Livestreaming',
                  104: 'Ticket booking', 105: 'Augmented reality', 106: 'Cross border ecommerce',
                  107: 'Fulfilment', 108: 'Ecommerce frontends', 109: 'Domain parking', 110: 'Form builders',
                  111: 'Fundraising & donations'}

    groups = {'Sales': {6, 41, 84, 91, 94, 98, 99, 102, 103, 106, 107, 108},
              'Marketing': {32, 36, 53, 54, 71, 75, 76, 77, 78, 86, 90, 94, 96, 97},
              'Content': {1, 2, 4, 7, 8, 11, 13, 15, 21, 24, 29, 49, 50, 89},
              'Communication': {2, 30, 39, 46, 52, 75},
              'Utilities': {3, 9, 56},
              'Other': {5, 19, 58, 101, 109, 111},
              'Servers': {9, 22, 23, 28, 31, 33, 34, 37, 38, 45, 60, 62, 63, 64, 65, 88, 92},
              'Analytics': {10, 42, 73, 74, 83, 97, 110},
              'Web development': {12, 17, 18, 20, 25, 26, 27, 44, 47, 51, 57, 59, 66, 68, 85},
              'Media': {7, 14, 38, 48, 95, 103, 105},
              'Security': {16, 69, 70},
              'Privacy': {67},
              'Booking': {72, 93, 104},
              'Add-ons': {80, 81, 82, 87, 100},
              'Business tools': {52, 53, 55, 101},
              'Location': {35, 79},
              'User generated content': {2, 13, 15, 90, 96}}


    @staticmethod
    def parse_json(wappalyzer_log: dict, groups: list[str]) -> dict:
        # to do - берется url со статусом 200, но его может не быть...
        if not wappalyzer_log.get('technologies', []):
            return {}
        url = list(wappalyzer_log.get('urls').keys())[-1]                   
        result = {}
        protocol, addr = url.split('://')
        addr = addr.split('/')[0]
        if ':' in addr:
            addr, port = addr.split(':')
            result.update({'port' : int(port)})
        else:
            result.update({'port' : 443 if protocol == 'https' else 80})

        try:
            IPv4Address(addr)
            # to do bag с resolve домена, если в логах стутус 200, а при парсинге нет (пока отправляется либо домен, либо ip)
            # result.update({'ip' : DNS.proceed_records([await DNS.resolve_domain(addr, 'A')])[0].get("record_value")})
            result.update({'ip' : addr})
        except:
            result.update({'domain' : addr})

        categories_id = set()
        for name_categoty in groups:
            categories_id = set.union(categories_id, WappalyzerParser.groups.get(name_categoty))
        softwares: list[SoftwareStruct] = []
        for tech in wappalyzer_log.get('technologies', {}):
            cpe = tech.get('cpe', "")
            cpe_type = ""
            vendor = ""
            product = ""
            if cpe:
                cpe_type = {'a' : 'Applications', 'h' : 'Hardware', 'o' : 'Operating Systems'}.get(cpe.replace('/', '2.3:').split(':')[2])
                vendor = cpe.replace('/', '2.3:').split(':')[3]
                product = cpe.replace('/', '2.3:').split(':')[4]
            else:
                product = tech.get("slug", "")
            version = tech.get('version', "")
            if version: version = re.search("([0-9]{1,}[.]){0,}[0-9]{1,}", version).group(0)
            if product and version:
                list_cpe = CPEGuess.search(vendor=vendor, product=product, version=version, exact=True)
                cpe = ', '.join(list_cpe) if list_cpe else ""
                if cpe:
                    vendor = cpe.replace('/', '2.3:').split(':')[3]
            if any([int(category.get('id')) in categories_id for category in tech.get('categories')]):
                tmp_soft = SoftwareStruct()
                tmp_soft.type = cpe_type
                tmp_soft.vendor = vendor or ""
                tmp_soft.product = product or ""
                tmp_soft.version = version or ""
                tmp_soft.cpe23 = cpe or ""
                softwares.append(tmp_soft)
        result.update({'softwares' : softwares})
        return result


    @classmethod
    async def restruct_result(cls, data: dict):
        if not data:
            return []
        
        vendors = {}
        softwares = {}

        result = []
        port = data.get("port")
        domain = data.get("domain")
        ip = data.get("ip")

        if domain:
            new_domain = Domain(domain=domain)
            try:
                responses =  [await DNSModule.resolve_domain(domain=domain, record="A")]
                new_domain, new_ip, dns_a = DNSModule.proceed_records(domain, responses)
                result.extend([new_domain, new_ip, dns_a])
            except:
                result.append(new_domain)
        else:
            new_domain = Domain(domain="")
            result.append(new_domain)
        if ip:
            new_ip = IP(ip=ip)
            result.append(new_ip)
        else:
            new_ip = IP(ip="")
            result.append(new_ip)
        if port:
            new_port = Port(port=port, ip=new_ip)
            result.append(new_port)

        new_l7 = L7(port=new_port, domain=new_domain)
        result.append(new_l7)
        for software in data["softwares"]:
            soft = software.model_dump()
            if all(v is None for v in soft.values()) or (not software.vendor and not software.product):
                continue
            
            vendor_name = soft.pop("vendor")
                    
            if vendor_name and vendor_name in vendors:
                vendor_obj = vendors.get(vendor_name)
            else:
                vendor_obj = Vendor(name=vendor_name)
                vendors[vendor_name] = vendor_obj
                result.append(vendor_obj)
            
            hash_string = vendor_name or "" + "_" + "_".join([v for v in soft.values() if v])

            if not (hash_string and hash_string in softwares):
                soft_obj = Software(vendor=vendor_obj, **soft)
                softwares[hash_string] = soft_obj
                result.append(soft_obj)
                new_l7_soft = L7Software(l7=new_l7, software=soft_obj)
                result.append(new_l7_soft)
        return result

    @staticmethod
    def get_groups():
        return dict(sorted(WappalyzerParser.groups.items(), key=lambda x: x[0]))
    
    @staticmethod
    def get_categories_by_group():
        result = {}
        for group_name, ids in WappalyzerParser.groups.items():
            result.update({group_name : '\n'.join([name for id, name in WappalyzerParser.categories.items() if id in ids])})
        return result

    


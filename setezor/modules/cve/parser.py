

import json
from setezor.modules.acunetix.schemes.vulnerability import Vulnerability


class CveParser():

    @staticmethod
    def parse_vulners_logs(file_path: str) -> list:
        data = json.load(open(file_path))

        if data.get("result") != 'OK':
            return []

        res = data.get('data', {}).get('search', {})

        result = []
        for r in res:
            tmp = {'name': r.get('_source', {}).get('title'),
                   'cve': r.get('_source', {}).get('cvelist', [None])[0] if len(r.get('cvelist', [None])) == 1 else None,
                   'cwe': None,
                   'description': r.get('_source', {}).get('description'),
                   'details': r.get('_source').get('sourceData'),
                   'cvss': r.get('_source', None).get('cvss', {}).get("vectorString"),
                   'cvss2': r.get('_source', None).get('cvss2', {}).get('cvssV2', {}).get("vectorString"),
                   'cvss2_score': r.get('_source', None).get('cvss2', {}).get('cvssV2', {}).get("baseScore"),
                   'cvss3': r.get('_source', None).get('cvss3', {}).get('cvssV3', {}).get("vectorString"),
                   'cvss3_score': r.get('_source', None).get('cvss3', {}).get('cvssV3', {}).get("baseScore"),
                   'cvss4': r.get('_source', None).get('cvss4', {}).get('cvssV4', {}).get("vectorString"),
                   'cvss4_score': r.get('_source', None).get('cvss4', {}).get('cvssV4', {}).get("baseScore"),
                   'severity': None
                   }

            result.append(Vulnerability(**tmp).model_dump())
        return result

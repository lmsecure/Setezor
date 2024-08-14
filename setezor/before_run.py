from collections import namedtuple
import pkg_resources
import sys
import os
from setezor.tools.shell_tools import create_shell_subprocess


Package = namedtuple('Package', ['name', 'version'])


def check_nmap():
    try:
        res, err = create_shell_subprocess('nmap -V'.split()).communicate()
        if err:
            raise
        else:
            res, err = create_shell_subprocess('nmap --traceroute --privileged localhost'.split()).communicate()
            if err:
                print('You NMAP capabilities is limited. Some NMAP function will not worked. please run:\n\tsudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/bin/nmap')
            return True
    except:
        print('\tPlease install "nmap"')
        return False
        
def check_requirements_file(base_path: str):
    result = True
    local_modules = sorted([Package(i.key, i.version) for i in pkg_resources.working_set])
    with open(os.path.join(base_path, 'requirements.txt'), 'r') as f:
        requirements = [Package(i.key, i.specs[0][1]) for i in pkg_resources.parse_requirements(f.read())]
    not_installed = [r for r in requirements if all([r.name != m.name for m in local_modules])]
    diff_version = [(r.name, r.version, m.version) for r in requirements for m in local_modules if r.name == m.name and r.version != m.version]
    if not_installed:
        print('Find not installed requirements.\nYou must install next packages\n\t' + '\n\t'.join([f'{i.name}=={i.version}'for i in not_installed]))
        print()
        print([i.name for i in local_modules if 'dash' in i.name])
        result = False
    else:
        result = True
    if diff_version:
        print(f'Find difference with versions in packages.\n\t' + '\n\t'.join(['Installed "%s" version "%s", needed version "%s"' % i for i in diff_version]))
    return result


def check_software(base_path: str):
    if not all([check_nmap(), check_requirements_file(base_path)]):
        sys.exit(0)
    else:
        return
    

if __name__ == '__main__':
    check_software()
from tasks.nmap_command import NmapCommand, NmapScript
from timeit import timeit

script = NmapScript(name='acarsd-info')
command = NmapCommand(ports='161', target='192.168.105.2', flags=['-sU'], scripts=[script]) # type: ignore

print(command)
print(script)


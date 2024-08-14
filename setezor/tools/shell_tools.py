from subprocess import Popen, PIPE
import re
from asyncio import create_subprocess_shell as async_shell
from asyncio.subprocess import PIPE as asyncPIPE


def create_shell_subprocess(command: list):
    return Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf8')

async def create_async_shell_subprocess(command: list):
    return await async_shell(' '.join(command), stdin=asyncPIPE, stdout=asyncPIPE, stderr=asyncPIPE)


def check_superuser_previliges(password: str):
    res, err = create_shell_subprocess('timeout 0.1 sudo -S -v'.split()).communicate(password)
    if re.match(r'^\[sudo\] password for [^\n]+?$', err) or not err:
        return True
    else:
        return False
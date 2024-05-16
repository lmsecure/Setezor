from typing import Annotated
import shlex

from pydantic import BaseModel, Field, AfterValidator, model_validator, ConfigDict
from .nmap_scripts import NMAP_SCRIPTS

def __validate_flag(flag: str):
    if not flag.startswith("-"):
        raise ValueError(f'Flag must starts with "-", flag is <{flag}>')
    return flag


FLAG = Annotated[str, AfterValidator(__validate_flag)]


class NmapScript(BaseModel):
    
    model_config = ConfigDict(frozen=True)
    
    name: NMAP_SCRIPTS  # в идеале выдернуть имена и хранить в Literal иди Enum
    params: tuple[str] = Field(default_factory=tuple)

    def __str__(self):
        params = shlex.join(self.params)
        return f"--script={shlex.quote(self.name)} {params}"


class NmapCommand(BaseModel):
    ports: str = Field(pattern="^[\d,\-]+$") # type: ignore
    target: str = Field(min_length=7)
    privileged: bool = True
    sudo: bool = False
    scripts: set[NmapScript] = Field(default_factory=set)
    flags: set[FLAG] = Field(default_factory=set)

    @model_validator(mode="after")
    def root_validator(self):
        assert self.sudo != self.privileged, "Only sudo or privileged can be used!"
        return self

    def __str__(self):
        sudo = "--privileged" if self.privileged else ""
        priv = "sudo" if self.sudo else ""
        flags = shlex.join(self.flags)
        output = "-oX -"
        ports = f"-p {self.ports}"
        scripts = ''.join((str(i) for i in self.scripts))
        command = f"nmap {sudo} {priv} {output} {flags} {self.target} {ports} {scripts}"
        return command

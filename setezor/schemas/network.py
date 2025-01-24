from pydantic import BaseModel
from setezor.network_structures import InterfaceStruct

class InterfaceResponse(BaseModel):
    interfaces: list[InterfaceStruct]
    default_interface: int
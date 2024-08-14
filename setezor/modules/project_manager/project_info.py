from typing import Any
from dataclasses import dataclass, field, asdict

@dataclass(slots=True, unsafe_hash=True, eq=True)
class ProjectInfo:
    
    name: str
    project_id: str
    object_count: int
    ip_count: int
    mac_count: int
    port_count: int
    
    top_object_type: list['FrequentValue'] = field(default_factory=list)
    top_ports: list['FrequentValue'] = field(default_factory=list)
    top_protocols: list['FrequentValue'] = field(default_factory=list)
    top_products: list['FrequentValue'] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)


@dataclass(slots=True, unsafe_hash=True, eq=True)
class FrequentValue:
    
    column: str
    value: Any
    count: int
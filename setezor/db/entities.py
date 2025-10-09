from enum import StrEnum


class ObjectTypes(StrEnum):
    unknown: str =        "3d9cf6c43fd54aacb88878f5425f43c4"
    router: str =         "0f53be90b5534091844969585a109ccc"
    switch: str =         "5a3edb2b46dd43a38a62d15263204512"
    win_server: str =     "50eabecb80f345709c55fea37106ff4c"
    linux_server: str =   "9931d00b80264046a2a2729c190110a8"
    firewall: str =       "0391e3dd460241eea140dd0bf2786c84"
    win_pc: str =         "5794843deda7454dbad181a012f8f914"
    linux_pc: str =       "73b6106cc1fa4f129683548f3f2d3184"
    nas: str =            "4681b1c682a0445b8242a0cfa3888b86"
    ip_phone: str =       "2a2713215d624cb7a74c6918e37e2ecf"
    printer: str =        "f3cc1e8288ef46a6a0355061fb1272f3"
    tv: str =             "0a295b4782384fa895effe7f89fc0fc8"
    android_device: str = "2489848fd5a342fdb75881c6e2c7b30f"


class NetworkTypes(StrEnum):
    external: str =  "b271a925283445c5ab60782a42466bfc"
    internal: str =  "08d6fdf488004017b707d42c2cc551b7"
    perimeter: str = "6fa8cc94fce744fb815057c6376666a9"


class DNSTypes(StrEnum):
    A: str =     "5e4fe7edfbac4860ac10b2b5eadbae6c"
    NS: str =    "b009db7871d249268fbf92291bbc5512"
    MX: str =    "88eab15bfb914f1baf4767cd825108f0"
    CNAME: str = "658376456248484f97b0d796d67cffd3"
    SOA: str =   "bc1f296de6a349e5a5b71ebeb463fe6b"
    TXT: str =   "d500afc6595d4c6a930cce0402b0a89b"
    AAAA: str =  "61e073bd02554e81a89d37e6ba9fe9b4"
    SRV: str =   "de4157e83f104bc096722cd1bd8713c4"
    PTR: str =   "22857212261a437d9d8733fb9a7e89b0"

import orjson
from pydantic import BaseModel

def handle_dump(value):
    assert hasattr(value, '__str__')
    return str(value)

def orjson_dumps(data: dict, *args, **kwargs):
    return orjson.dumps(data, default=handle_dump).decode()

def orjson_loads(data, *args, **kwargs):
    return orjson.loads(data)

import orjson


def orjson_dumps(data: dict, *args, **kwargs):
    return orjson.dumps(data, default=lambda value: str(value)).decode()


def orjson_loads(data, *args, **kwargs):
    return orjson.loads(data)

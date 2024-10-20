from typing import TypeVar, Generic, Callable, Any, ParamSpec
import inspect

from aiohttp import web
import aiohttp
from pydantic import TypeAdapter
import orjson

from setezor.tools.ip_tools import get_default_interface, get_ipv4


MACHINE_IP = get_ipv4(get_default_interface())
_P = ParamSpec("_P")
_Returns = TypeVar("_Returns")


class SpyMethod(Generic[_P, _Returns]):
    def __init__(self, func: Callable[_P, _Returns]) -> None:
        self._func = func
        self.__kwargs_adapters = {k: TypeAdapter(v) for k, v in self._func.__annotations__.items() if k != 'return'}
        self.__return_adapter = TypeAdapter(func.__annotations__['return'])

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _Returns:
        return self._func(*args, **kwargs)
    
    async def run_on_agent(self, agent_ip: str, agent_port: int, *args: _P.args, **kwargs: _P.kwargs) -> _Returns:
        if agent_ip != MACHINE_IP: # для теста на локальной машине поменять, тогда все вызовы будут идти через спай
            url = self._format_url(agent_ip, agent_port)
            kwargs = self.__format_args_to_kwargs(self._func, *args, **kwargs)
            for var_name, adapter in self.__kwargs_adapters.items():
                if var_name in kwargs:
                    kwargs[var_name] = adapter.dump_python(kwargs[var_name])
            return await self.__make_request(url, **kwargs)
        else:
            return await self._func(*args, **kwargs)

    @property
    def server_path(self) -> str:
        return '/' + self._func.__qualname__.replace('.', '/')
    
    def _format_url(self, agent_ip: str, agent_port: int) -> str:
        return f'http://{agent_ip}:{agent_port}{self.server_path}'

    def __format_args_to_kwargs(self, func: Callable, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Converts positional and keyword arguments into a dictionary of keyword arguments,
        including default values for those not provided explicitly.
        """
        signature = inspect.signature(func)
        bound_args = signature.bind(*args, **kwargs)
        formatted_kwargs = {name: value for name, value in bound_args.arguments.items()}

        for param in signature.parameters.values():
            if param.name not in formatted_kwargs:
                if param.default is not inspect.Parameter.empty:
                    formatted_kwargs[param.name] = param.default

        return formatted_kwargs
    
    async def __make_request(self, url: str, **kwargs: Any) -> _Returns:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=orjson.dumps(kwargs)) as response:
                return self.__return_adapter.validate_json(await response.read())
            
    def __server_function__(self) -> Callable[[web.Request], web.Response]:
        async def handler(request: web.Request) -> web.Response:
            data = await request.read()
            kwargs = orjson.loads(data)
            for var_name, adapter in self.__kwargs_adapters.items():
                if var_name in kwargs:
                    kwargs[var_name] = adapter.validate_python(kwargs[var_name])
            result = await self(**kwargs)
            return_data = self.__return_adapter.dump_json(result)
            return web.Response(body=return_data, content_type='application/json')
        return handler
            

class Spy:
    _methods: list[SpyMethod] = []
    
    @classmethod
    def spy_method(cls, func: Callable[_P, _Returns]) -> SpyMethod[_P, _Returns]:
        method = SpyMethod(func)
        cls._methods.append(method)
        return method
    
    def serve(self, host: str, port: int) -> None:
        app = web.Application()
        routes = []
        for method in self._methods:
            routes.append(web.route('POST', method.server_path, method.__server_function__()))
        app.add_routes(routes)
        web.run_app(app, host=host, port=port)
        

spy = Spy()

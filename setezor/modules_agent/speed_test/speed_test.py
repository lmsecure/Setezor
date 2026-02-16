import os
import ctypes
import asyncio


class Client:
    lib_path = os.path.join(os.path.dirname(__file__), "speed_test_lib.module")
    lib = ctypes.CDLL(lib_path)

    lib.start_sender.argtypes = [
        ctypes.c_char_p,    # client_id (task_id)
        ctypes.c_char_p,    # target_ip
        ctypes.c_int,       # target_port
        ctypes.c_int,       # duration
        ctypes.c_uint,      # packet_size
        ctypes.c_int,       # protocol
        ctypes.c_bool       # verbose
    ]
    lib.start_sender.restype = ctypes.c_bool

    lib.is_sender_work.argtypes = [ctypes.c_char_p]
    lib.is_sender_work.restype = ctypes.c_bool

    lib.finish_sender.argtypes = [ctypes.c_char_p]

    lib.getSenderErrorInfo.restype = ctypes.c_char_p


    @classmethod
    async def start(cls, client_id: str, target_ip: str, target_port: int = 13337, duration: int = 5, packet_size: int = 1400, protocol: int = 0, verbose: bool = True):
        is_start = cls.lib.start_sender(
            client_id.encode("utf-8"),
            target_ip.encode("utf-8"),
            target_port,
            duration,
            packet_size,
            protocol,
            verbose
        )
        if not is_start:
            raise Exception(cls.lib.getSenderErrorInfo().decode("utf-8"))

        while cls.lib.is_sender_work(client_id.encode("utf-8")):
            await asyncio.sleep(2)

        cls.lib.finish_sender(client_id.encode("utf-8"))

    @classmethod
    async def finish(cls, client_id: str):
        cls.lib.finish_sender(client_id.encode("utf-8"))


class Server:
    lib_path = os.path.join(os.path.dirname(__file__), "speed_test_lib.module")
    lib = ctypes.CDLL(lib_path)

    lib.start_server.argtypes = [
        ctypes.c_char_p,    # server_id (task_id)
        ctypes.c_int,       # target_port
        ctypes.c_int,       # protocol
        ctypes.c_bool       # verbose
    ]
    lib.start_server.restype = ctypes.c_bool

    lib.is_server_work.argtypes = [ctypes.c_char_p]
    lib.is_server_work.restype = ctypes.c_bool

    lib.finish_server.argtypes = [ctypes.c_char_p]

    lib.getServerErrorInfo.restype = ctypes.c_char_p

    lib.get_result.argtypes = [ctypes.c_char_p]
    lib.get_result.restype = ctypes.c_double

    @classmethod
    async def start(cls, server_id: str, target_port: int = 13337, protocol: int = 0, verbose: bool = True) -> float:
        is_start = cls.lib.start_server(
            server_id.encode("utf-8"),
            target_port,
            protocol,
            verbose
        )
        if not is_start:
            raise Exception(cls.lib.getServerErrorInfo().decode("utf-8"))

        while cls.lib.is_server_work(server_id.encode("utf-8")):
            await asyncio.sleep(2)
        return cls.lib.get_result(server_id.encode("utf-8"))


    @classmethod
    async def finish(cls, server_id: str):
        cls.lib.finish_server(server_id.encode("utf-8"))

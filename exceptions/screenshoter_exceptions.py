import traceback

class ConnectionError(Exception):
    def __init__(self, url: str, message: str):
        self.message = f'Can not connect to {url}. Exception text:\n{message}'

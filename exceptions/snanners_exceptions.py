import traceback


class NmapCommandError(Exception):
    def __init__(self, message: str):
        self.message = message


class NmapParserError(Exception):
    def __init__(self):
        self.message = traceback.format_exc()


class NmapSaverError(Exception):
    def __init__(self, filepath: str):
        self.message = f'Could not create file by path "{filepath}"'

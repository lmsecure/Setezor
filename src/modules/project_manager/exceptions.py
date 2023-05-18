


class FileNotExistsError(Exception):
    message = ''
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class FileSaveError(Exception):
    message = ''
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ConfigLoadError(Exception):
    message = ''
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class t(Exception):
    message = ''
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

import os
from exceptions.loggers import get_logger


class FilesStructure:
    """Класс для работы с файлов структурой проекта
    """    
    
    def __init__(self, folders: dict, files: dict):
        self.folders = folders
        self.files = files
        self.logger = get_logger(self.__module__, handlers=[])
        
    def create_project_structure(self) -> None:
        """Метод создания файловой структуры проекта
        """        
        for key, value in self.folders.items():
            self.__create_folder_in_project_folder(value)
        for key, value in self.files.items():
            self.__create_file_in_project_folder(value)
    
    def check_project_structure(self) -> bool:
        """метод проверки файловой структуры проекта

        Returns:
            bool: результат проверки
        """        
        not_exists = []
        for key, value in {**self.folders, **self.files}.items():
            if not os.path.exists(value):
                not_exists.append(value)
        return not bool(not_exists), not_exists
    
    def __create_file_in_project_folder(self, path: str) -> None:
        """Метод создания файла

        Args:
            path (str): путь до файла
        """        
        self.__create_folder_in_project_folder('/'.join(path.split('/')[:-1]))
        if not self.__check_path_in_project_folder(path):
            f = open(path, 'w')
            f.close()
            self.logger.debug('Created in project file')
        
    def __create_folder_in_project_folder(self, path: str):
        """Метод создания папки

        Args:
            path (str): путь до папки
        """        
        if not self.__check_path_in_project_folder(path):
            os.makedirs(path, exist_ok=True)
            self.logger.debug('Created in project folder "%s"', path)
        
    def __check_path_in_project_folder(self, path: str):
        """Метод проверки существования папки или файла по пути

        Args:
            path (str): путь до папки или файла

        Returns:
            _type_: _description_
        """        
        return os.path.exists(path)
        


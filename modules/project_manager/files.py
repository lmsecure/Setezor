import os
from .structure import Folders, Files


class FilesStructure:
    """Класс для работы с файлов структурой проекта
    """    
    
    def __init__(self, folders: Folders, files: Files):
        self.folders = folders
        self.files = files
        
    def create_project_structure(self) -> None:
        """Метод создания файловой структуры проекта
        """        
        for folder in self.folders:
            self.__create_folder_in_project_folder(folder)
        for file in self.files:
            self.__create_file_in_project_folder(file)
    
    def check_project_structure(self) -> bool:
        """метод проверки файловой структуры проекта

        Returns:
            bool: результат проверки
        """        
        not_exists = []
        for value in [*self.folders, *self.files]:
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
        
    def __create_folder_in_project_folder(self, path: str):
        """Метод создания папки

        Args:
            path (str): путь до папки
        """        
        if not self.__check_path_in_project_folder(path):
            os.makedirs(path, exist_ok=True)
        
    def __check_path_in_project_folder(self, path: str):
        """Метод проверки существования папки или файла по пути

        Args:
            path (str): путь до папки или файла

        Returns:
            _type_: _description_
        """        
        return os.path.exists(path)
        


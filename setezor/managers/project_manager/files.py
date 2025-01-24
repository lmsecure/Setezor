import os
from .structure import Folders


class FilesStructure:
    """Класс для работы с файлов структурой проекта
    """
    @classmethod
    def create_project_structure(cls, path: str) -> None:
        """Метод создания файловой структуры проекта
        """
        for folder in Folders:
            new_folder = os.path.join(path, folder.value)
            cls.__create_folder_in_project_folder(new_folder)
        # for file in self.files:
        #    self.__create_file_in_project_folder(file)
    
    @classmethod
    def __create_file_in_project_folder(cls, path: str) -> None:
        """Метод создания файла

        Args:
            path (str): путь до файла
        """
        cls.__create_folder_in_project_folder('/'.join(path.split('/')[:-1]))
        if not cls.__check_path_in_project_folder(path):
            f = open(path, 'w')
            f.close()

    @classmethod
    def __create_folder_in_project_folder(cls, path: str):
        """Метод создания папки

        Args:
            path (str): путь до папки
        """
        if not cls.__check_path_in_project_folder(path):
            os.makedirs(path, exist_ok=True)

    @classmethod
    def __check_path_in_project_folder(cls, path: str):
        """Метод проверки существования папки или файла по пути

        Args:
            path (str): путь до папки или файла

        Returns:
            _type_: _description_
        """
        return os.path.exists(path)

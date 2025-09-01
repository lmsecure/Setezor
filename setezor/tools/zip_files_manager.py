import os
from io import BytesIO

from zipfile import ZipFile, ZipInfo


class ZipFileManager:

    def pack_folder_to_bytes(self, folder_path: str) -> BytesIO:
        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, 'w') as myzip:
            for root, dirs, files in os.walk(folder_path):
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    arcname = os.path.relpath(dir_path, start=folder_path) + '/'
                    myzip.writestr(ZipInfo(arcname), '')

                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=folder_path)
                    myzip.write(file_path, arcname=arcname)

        zip_buffer.seek(0)
        return zip_buffer

    def add_file(self, zip_buffer: BytesIO, file_name: str, file) -> BytesIO:
        zip_buffer.seek(0)

        with ZipFile(zip_buffer, 'a') as myzip:
            myzip.writestr(file_name, file)

        zip_buffer.seek(0)
        return zip_buffer

    def unpack_files(self, path: str, zip_buffer: BytesIO):
        os.makedirs(path, exist_ok=True)
        with ZipFile(zip_buffer, 'r') as zipf:
            zipf.extractall(path=path)

    @classmethod
    def new_instance(cls):
        return cls()
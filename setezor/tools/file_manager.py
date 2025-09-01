import os
import shutil


class FileManager:

    def merge_dirs(self, path_from: str, path_to: str):

        if not os.path.isdir(path_from) or not os.path.exists(path_from):
            raise Exception(f'Path {path_from} does not exist or is not a directory')

        os.makedirs(path_to, exist_ok=True)

        for root, dirs, files in os.walk(path_from):
            rel_path = os.path.relpath(root, path_from)
            target_root = os.path.join(path_to, rel_path)
            os.makedirs(target_root, exist_ok=True)

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_root, file)
                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)

    def remove_dir(self, path: str):

        if not os.path.isdir(path) or not os.path.exists(path):
            raise Exception(f'Path {path} does not exist or is not a directory')

        shutil.rmtree(path)

    @classmethod
    def new_instance(cls):
        return cls()
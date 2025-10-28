import os
from setezor.settings import PROJECTS_DIR_PATH


class ProjectFolders:
    @classmethod
    def create(cls, project_id: str):
        new_project_path = cls.get_path_for_project(project_id=project_id)
        if not os.path.exists(new_project_path):
            os.makedirs(new_project_path, exist_ok=True)

    @classmethod
    def get_projects_path(cls):
        return PROJECTS_DIR_PATH

    @classmethod
    def get_path_for_project(cls, project_id: str):
        PROJECTS_PATH = cls.get_projects_path()
        new_project_path = os.path.join(PROJECTS_PATH, project_id)
        if not os.path.exists(new_project_path):
            os.makedirs(new_project_path, exist_ok=True)
        return new_project_path
import datetime
import io
import os
import pickle
import aiofiles
from setezor.managers.project_manager.project_manager import ProjectFolders
from setezor.models.task import Task
from setezor.schemas.task import TaskStatus
from setezor.services.data_structure_service import DataStructureService
from setezor.services.task_service import TasksService
from setezor.tasks import get_folder_for_task
from setezor.unit_of_work.unit_of_work import UnitOfWork


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        full_name = f"{module}.{name}"
        if (full_name.startswith("setezor") or
                    full_name.startswith("sqlalchemy") or
                    full_name.startswith("datetime")
                ):
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Недопустимый класс: {full_name}")


def restricted_loads(data):
    file_like = io.BytesIO(data)
    return RestrictedUnpickler(file_like).load()


class TaskResultWriter:
    @classmethod  # метод сервера на запись результата на сервере
    async def write_result(cls, task_id: str, data: bytes, uow: UnitOfWork):
        result = restricted_loads(data)
        task: Task = await TasksService.get_by_id(uow=uow, id=task_id)
        project_id = task.project_id
        scan_id = task.scan_id
        service = DataStructureService(uow=uow, 
                                       project_id=project_id, 
                                       scan_id=scan_id, 
                                       result=result)
        await service.make_magic()
        await TasksService.set_status(uow=uow, 
                                      id=task_id, 
                                      status=TaskStatus.finished, 
                                      project_id=project_id)

    @classmethod  # метод сервера на запись сырых данных результата на сервере
    async def write_raw_result(cls, 
                               task_id: str, 
                               data: bytes, 
                               extension: str, 
                               uow: UnitOfWork):
        task: Task = await TasksService.get_by_id(uow=uow, id=task_id)
        project_id = task.project_id
        scan_id = task.scan_id
        created_by = task.created_by
        project_path = ProjectFolders.get_path_for_project(project_id)
        scan_project_path = os.path.join(project_path, scan_id)
        if not os.path.exists(scan_project_path):
            os.makedirs(scan_project_path, exist_ok=True)
        module_folder = get_folder_for_task(created_by)
        filename = f"{str(datetime.datetime.now())}_{created_by}_{task_id}"
        module_folder_path = os.path.join(project_path, 
                                 scan_project_path, 
                                 module_folder)
        if not os.path.exists(module_folder_path):
            os.makedirs(module_folder_path, exist_ok=True)
        file_path = os.path.join(module_folder_path, 
                                 filename) + f".{extension}"
        async with aiofiles.open(file_path, 'wb') as file:
            await file.write(data)

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
from setezor.tasks import get_folder_for_task, get_restructor_for_task
from setezor.unit_of_work.unit_of_work import UnitOfWork


class TaskResultWriter:
    @classmethod  # метод сервера на запись результата на сервере
    async def write_result(cls, task_id: str, data: dict, uow: UnitOfWork):
        task: Task = await TasksService.get_by_id(uow=uow, id=task_id)
        project_id = task.project_id
        scan_id = task.scan_id
        restructor = get_restructor_for_task(task.created_by)
        entities = await restructor.restruct(**data)
        service = DataStructureService(uow=uow, 
                                       project_id=project_id, 
                                       scan_id=scan_id, 
                                       result=entities)
        await service.make_magic()
        await TasksService.set_status(uow=uow, 
                                      id=task_id, 
                                      status=TaskStatus.finished)

    @classmethod  # метод сервера на запись сырых данных результата на сервере
    async def write_raw_result(cls,
                               task_id: str,
                               data: str,
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
        restructor = get_restructor_for_task(task.created_by)
        data = restructor.get_raw_result(data)
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

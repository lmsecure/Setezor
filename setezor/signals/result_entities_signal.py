import datetime
import json
import traceback

from setezor.logger import logger
from setezor.models import Task
from setezor.schemas.task import TaskStatus, WebSocketMessage, TaskNotify
from setezor.settings import PROJECTS_DIR_PATH
from setezor.signals.base_signal import Signal
from setezor.tasks.base_job import BaseJob
from setezor.tools.websocket_manager import WS_USER_MANAGER


class ResultEntitiesSignal(Signal):

    async def __call__(self, data: dict, task: Task, **kwargs):
        await self.tasks_service.set_status(id=task.id, status=TaskStatus.processing_on_server)
        message = WebSocketMessage(
            title="Task status",
            text=TaskNotify(id=task.id, name=task.created_by, status=TaskStatus.processing_on_server, traceback=task.traceback).to_str(),
            type="info"
        )
        await self.notify_by_websocket(message, task)
        try:
            task_data = data["result"]
            if (raw_result := task_data.get("raw_result")) and (
            extension := data.get("raw_result_extension")):
                await self.write_raw_result(task=task, data=raw_result, extension=extension)
            await self.write_result(task=task, data=task_data)
            await self.tasks_service.set_status(id=task.id, status=TaskStatus.finished)
            logger.info(f'FINISHED TASK {task.id}')
            message = WebSocketMessage(
                title="Task status",
                text=TaskNotify(id=task.id, name=task.created_by, status=TaskStatus.finished, traceback=task.traceback).to_str(),
                type="success"
            )
            await self.notify_by_websocket(message, task)
            if task.created_by == 'PushModuleTask':
                module_name = json.loads(task.params)['module_name']
                message = WebSocketMessage(
                    title="Install module",
                    text=f"Module {module_name} successfully installed",
                    type="success"
                )
                await WS_USER_MANAGER.send_message(entity_id=task.user_id, message=message)
        except Exception:
            logger.error(f'FAILED TASK {task.id}', exc_info=False)
            traceback_str = traceback.format_exc()
            await self.tasks_service.set_status(
                id=task.id,
                status=TaskStatus.failed,
                traceback=traceback_str[-1000:]
            )
            message = WebSocketMessage(
                title="Task status",
                text=TaskNotify(id=task.id, name=task.created_by, status=TaskStatus.failed, traceback=traceback_str[-200:]).to_str(),
                type="error"
            )
            await WS_USER_MANAGER.send_message(entity_id=task.user_id, message=message)

    async def write_result(self, task: Task, data: dict):
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        project_id = task.project_id
        scan_id = task.scan_id
        if not data.get('agent_id'):
            data['agent_id'] = task.agent_id
        data["project_id"] = project_id
        data["scan_id"] = scan_id
        data["user_id"] = task.user_id
        data["task_id"] = task.id
        if not task_class.restructor:
            logger.debug(f"Task {task.created_by} {task.id} does not have restructor")
            return
        entities = await task_class.restructor.restruct(**data)
        await self.data_structure_service.make_magic(
            project_id=project_id,
            scan_id=scan_id,
            result=entities
        )

    async def write_raw_result(self, task: Task, data: str, extension: str):
        task_class = BaseJob.get_task_by_class_name(task.created_by)
        if not task_class.restructor:
            logger.debug(f"Task {task.created_by} {task.id} does not have restructor")
            return
        data = task_class.restructor.get_raw_result(data)
        filename = f"{str(datetime.datetime.now())}_{task.created_by}_{task.id}"
        await self.file_manager.save_file(
            file_path=[
                PROJECTS_DIR_PATH, task.project_id, task.scan_id,
                task_class.logs_folder, f"{filename}.{extension}"
            ],
            data=data
        )
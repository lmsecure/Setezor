import os

from fastapi.responses import FileResponse
from fastapi import HTTPException

from setezor.models import Task
from setezor.modules.site_parser.web_archive import WebArchiveModule
from setezor.services.base_service import BaseService
from setezor.settings import PROJECTS_DIR_PATH


class WebArchiveService(BaseService):

    async def get_web_archive(self, task_id: str, user_id: str, project_id: str) -> FileResponse:
        async with self._uow:
            task: Task = await self._uow.task.find_one(id=task_id, user_id=user_id)
            if not task:
                raise HTTPException(status_code=404, detail='Task not found')

            archive_name = WebArchiveModule.get_file_name_by_task_id(
                project_id=project_id, scan_id=task.scan_id, task_id=task_id
            )
            archive_path = os.path.join(PROJECTS_DIR_PATH, project_id, task.scan_id, 'web_archives', archive_name)
        return FileResponse(path=archive_path, media_type='application/json', filename=archive_name)
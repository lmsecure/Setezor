import os
import sys
import tempfile
import asyncio
import shutil
import base64
import json
import io
from io import BytesIO

from typing import Annotated, Callable
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse

from setezor.tools.websocket_manager import WS_USER_MANAGER, WS_MANAGER
from setezor.schemas.task import WebSocketMessage
from setezor.managers.task_manager import TaskManager
from setezor.services import AgentService, AgentInProjectService
from setezor.tools.zip_files_manager import ZipFileManager
from setezor.dependencies.project import check_role
from setezor.schemas.roles import Roles

from setezor.tasks.push_module_task import PushModuleTask

from setezor.settings import BASE_PATH

from setezor.tasks.base_job import BaseJob



class ModuleManager:
    def __init__(
        self,
        task_manager: TaskManager,
        agent_service: AgentService,
        agent_in_project_service: AgentInProjectService,
        zip_file_manager: ZipFileManager
    ):
        self.available_modules = set(os.listdir(os.path.join(BASE_PATH, "modules_agent")))
        self.__task_manager: TaskManager = task_manager
        self.__agent_service: AgentService = agent_service
        self.__agent_in_project_service: AgentInProjectService = agent_in_project_service
        self.__zip_file_manager: ZipFileManager = zip_file_manager


    @classmethod
    async def new_instance(
        cls,
        task_manager:  Annotated[TaskManager, Depends(TaskManager.new_instance)],
        agent_service:  Annotated[AgentService, Depends(AgentService.new_instance)],
        agent_in_project_service: Annotated[AgentInProjectService, Depends(AgentInProjectService.new_instance)],
        zip_file_manager: Annotated[ZipFileManager, Depends(ZipFileManager.new_instance)]
    ):
        return cls(
            task_manager=task_manager,
            agent_service=agent_service,
            agent_in_project_service=agent_in_project_service,
            zip_file_manager=zip_file_manager
        )

    async def _get_depends(self,
                    module_path: str,
                    agent_info: dict,
                    prepare_module: Callable | None = None) -> BytesIO:
        platform_tag = agent_info.get("platform_tag")
        python_version = agent_info.get("python_version")
        implementation = agent_info.get("implementation")
        abi = agent_info.get("abi")
        with tempfile.TemporaryDirectory() as tmp:
            dst_root = os.path.join(tmp, os.path.basename(module_path))
            if os.path.exists(dst_root):
                os.rmdir(dst_root)
            shutil.copytree(module_path, dst_root)
            requirements = os.path.join(dst_root, "requirements.txt")
            if os.path.isfile(requirements):
                external_dir = os.path.join(dst_root, "external")
                if not os.path.isdir(external_dir):
                    os.mkdir(external_dir)
                cmd = [
                    sys.executable,
                    "-m", "pip", "install",
                    "--only-binary=:all:",
                    "--platform", platform_tag,
                    "--python-version", python_version,
                    "--implementation", implementation,
                    "--abi", abi,
                    "--target", external_dir,
                    "-r", requirements,
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(stderr.decode())
            await prepare_module(module_path=dst_root, agent_info=agent_info)
            return self.__zip_file_manager.pack_folder_to_bytes(tmp)

    def _stream_bytes(self, buf: io.BytesIO, chunk_size=1024 * 1024):
        buf.seek(0)
        while chunk := buf.read(chunk_size):
            yield chunk


    async def get_available_modules(self, agent_id, user_id) -> list[dict]:
        result = []
        modules: list[dict] = await self.__agent_service.get_available_modules(agent_id=agent_id, user_id=user_id)
        for module in modules:
            if module.get("module_name") in self.available_modules:
                result.append(module)
        return result


    async def install_modules(self, user_id: str, agent_id: str, modules: list[str], project_id: str | None = None) -> None:
        if project_id:
            if not check_role(role_require=[Roles.owner, Roles.executor], project_id=project_id, user_id=user_id) \
            or not self.__agent_in_project_service.is_agent_in_project(agent_id=agent_id, project_id=project_id):
                message = WebSocketMessage(title="Error", text=f"Access denied",
                                           type="error", user_id=user_id)
                await WS_MANAGER.send_message(entity_id=project_id, message=message)
        if not project_id:
            await self.__agent_service.user_own_agent(agent_id=agent_id, user_id=user_id)
        uninstalled_modules = await self.__agent_service.get_uninstalled_modules(agent_id=agent_id, user_id=user_id, modules=modules)
        for module_name in uninstalled_modules:
            if module_name in self.available_modules:
                await self.__task_manager.create_job(
                    job=PushModuleTask,
                    user_id=user_id,
                    agent_id=agent_id,
                    project_id=project_id,
                    scan_id=None,
                    signal="create_job",
                    module_name=module_name
                )
            else:
                message = WebSocketMessage(title="Error", text=f"Not exist module",
                                        type="error", user_id=user_id, command="notify_user")
                await WS_USER_MANAGER.send_message(entity_id=user_id, message=message)

    async def get_module(self, agent_id: str, module_name: str) -> StreamingResponse:
        module_path = os.path.join(BASE_PATH, "modules_agent", module_name)
        if not os.path.exists(module_path):
            raise HTTPException(status_code=404, detail="Not found module")
        agent_obj = await self.__agent_service.get_by_id(id=agent_id)
        if not agent_obj:
            agent_in_project = await self.__agent_in_project_service.get_by_id(agent_id=agent_id)
            agent_obj = agent_in_project.agent

        if not agent_obj:
            raise HTTPException(status_code=404, detail="Agent not found")
        agent_info = json.loads(agent_obj.information)
        task_name = [task_name for task_name, value in agent_info.get("tasks").items() if value.get("module_name") == module_name][0]
        task = BaseJob.get_task_by_class_name(task_name)
        module = await self._get_depends(
            module_path=module_path,
            agent_info=agent_info,
            prepare_module=task.prepare_module
        )
        if not module:
            raise FileNotFoundError(f"Module {module_name} not found.")
        return StreamingResponse(
            self._stream_bytes(module),
            media_type="application/octet-stream"
        )

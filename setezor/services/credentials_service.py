from setezor.interfaces.service import IService
from setezor.unit_of_work.unit_of_work import UnitOfWork
from setezor.models.auth_credentials_resource import Authentication_Credentials



class CredentialsService(IService):

    @classmethod
    async def get_credentials_for_node(cls, uow: UnitOfWork, ip_id: str, project_id: str):
        async with uow:
            credentials = await uow.authentication_credentials.get_credentials_for_node(ip_id, project_id)
        result = []
        for port, credo in credentials:
            result.append({
                "port" : port.port,
                "protocol" : port.protocol,
                "login" : credo.login,
                "password" : credo.password or "",
                "need_auth" : ["no", "yes"][credo.need_auth],
                "permissions" : ("no permissions", "read", "write", "read/write")[credo.permissions],
                "parameters" : credo.parameters
            })
        return result


    @classmethod
    async def add_credentials(cls, uow: UnitOfWork, project_id: str, data: dict) -> dict:
        async with uow:
            port_obj = await uow.port.find_one(project_id=project_id, id=data.get("port_id"))
        data.update({"scan_id" : port_obj.scan_id})
        async with uow:
            new_credentials_obj = Authentication_Credentials(project_id=project_id, **data)
            uow.authentication_credentials.add(data=new_credentials_obj.model_dump())
            await uow.commit()
        res = {
                "port" : port_obj.port,
                "protocol" : port_obj.protocol,
                "login" : new_credentials_obj.login,
                "password" : new_credentials_obj.password or "",
                "need_auth" : ["no", "yes"][new_credentials_obj.need_auth],
                "permissions" : ("no permissions", "read", "write", "read/write")[new_credentials_obj.permissions],
                "parameters" : new_credentials_obj.parameters
        }
        return res
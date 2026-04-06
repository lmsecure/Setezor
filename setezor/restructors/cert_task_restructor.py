from setezor.modules.osint.cert.crt4 import CertInfo
from setezor.schemas.task import WebSocketMessage
from setezor.tools.websocket_manager import WS_MANAGER



class CertTaskRestructor:

    @classmethod
    async def restruct(cls, project_id: str, scan_id: str, agent_id: str, raw_result, data: dict, **kwargs):
        try:
            cert_data = CertInfo.parse_cert(cert=raw_result)
        except Exception as e:
            message = WebSocketMessage(title="Error",
                                       text="Cert not found",
                                       type="error")
            await WS_MANAGER.send_message(entity_id=kwargs['project_id'], message=message)
            raise Exception("Cert not found")

        result = await CertInfo.restruct(project_id=project_id, scan_id=scan_id, agent_id=agent_id,
                                data=data, cert_data=cert_data)
        return result


    @classmethod
    def get_raw_result(cls, data):
        return data.encode()

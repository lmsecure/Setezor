
import hashlib
from setezor.interfaces.service import IService
from setezor.models.invite_link import Invite_Link
from setezor.settings import INVITE_LINK_EXPIRE_TIME
from setezor.tools.jwt import JWT_Tool
from setezor.unit_of_work.unit_of_work import UnitOfWork


class InviteLinkService(IService):
    @classmethod
    async def create_token(cls, uow: UnitOfWork, count_of_entries: int, payload: dict):
        token = JWT_Tool.create_jwt(data=payload, 
                                    expires_delta=INVITE_LINK_EXPIRE_TIME)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        async with uow:
            token_exists = await uow.invite_link.find_one(token_hash=token_hash)
            if token_exists:
                return {"token": token_hash} 
            invite_link_object = Invite_Link(token_hash=token_hash,
                                             count_of_entries=count_of_entries,
                                             token=token)
            uow.invite_link.add(invite_link_object.model_dump())
            await uow.commit()

        return {"token": token_hash}
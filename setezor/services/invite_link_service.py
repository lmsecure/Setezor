
from dataclasses import dataclass
import hashlib
from setezor.services.base_service import BaseService
from setezor.models.invite_link import Invite_Link
from setezor.settings import INVITE_LINK_EXPIRE_TIME
from setezor.tools.jwt import JWT_Tool


class InviteLinkService(BaseService):
    async def get_by_hash(self, token_hash: str):
        async with self._uow:
            invite_link = await self._uow.invite_link.find_one(token_hash=token_hash)
            return invite_link

    async def create_token(self, count_of_entries: int, payload: dict):
        token = JWT_Tool.create_jwt(data=payload,
                                    expires_delta=INVITE_LINK_EXPIRE_TIME)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        async with self._uow:
            token_exists = await self._uow.invite_link.find_one(token_hash=token_hash)
            if token_exists:
                return {"token": token_hash}
            invite_link_object = Invite_Link(token_hash=token_hash,
                                             count_of_entries=count_of_entries,
                                             token=token)
            self._uow.invite_link.add(invite_link_object.model_dump())
            await self._uow.commit()

        return {"token": token_hash}
    

    async def change_count_of_entries(self, token_id: str, new_count_of_entries: int):
        async with self._uow:
            await self._uow.invite_link.edit_one(id=token_id, data={"count_of_entries": new_count_of_entries})
            await self._uow.commit()

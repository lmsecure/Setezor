from setezor.models import Invite_Link
from setezor.repositories import SQLAlchemyRepository

class InviteLinkRepository(SQLAlchemyRepository[Invite_Link]):
    model = Invite_Link
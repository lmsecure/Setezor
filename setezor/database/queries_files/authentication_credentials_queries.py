from typing import Any
from sqlalchemy.orm.session import Session
from sqlalchemy import func, desc
from ..models import Authentication_Credentials
from .resource_queries import ResourceQueries
from .base_queries import BaseQueries
import pandas as pd


class AuthenticationCredentialsQueries(BaseQueries):
    model = Authentication_Credentials

    def __init__(self, session_maker: Session):
        super().__init__(session_maker)

    @BaseQueries.session_provide
    def create(self, session: Session, **kwargs):
        new_auth_cred_obj = self.model(**kwargs)
        session.add(new_auth_cred_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, kwargs)
        return new_auth_cred_obj

    def get_headers(self) -> list:
        return [{},]

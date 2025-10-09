import os

from alembic import command
from alembic.config import Config
from setezor.settings import ALEMBIC_INI_PATH


class AlembicManager:
    
    @classmethod
    def history(cls):
        config = Config(ALEMBIC_INI_PATH)
        command.history(config)

    @classmethod
    def current(cls):
        config = Config(ALEMBIC_INI_PATH)
        command.current(config)

    @classmethod
    def revision(cls, autogenerate: bool, message: str = None):
        alembic_cfg = Config(ALEMBIC_INI_PATH)
        script_location = alembic_cfg.get_main_option("script_location")
        if not os.path.isabs(script_location):
            alembic_cfg.set_main_option(
                "script_location",
                os.path.join(os.getcwd(), script_location)
            )
        command.revision(
            alembic_cfg,
            message=message,
            autogenerate=autogenerate
        )


    @classmethod
    def stamp(cls, revision: str):
        config = Config(ALEMBIC_INI_PATH)
        command.stamp(config, revision)

    @classmethod
    def upgrade(cls, revision: str):
        config = Config(ALEMBIC_INI_PATH)
        command.upgrade(config, revision)

    @classmethod
    def downgrade(cls, revision: str):
        config = Config(ALEMBIC_INI_PATH)
        command.downgrade(config, revision)
import asyncio
from sqlalchemy import Column
from sqlalchemy.orm.relationships import Relationship
from sqlalchemy.orm.collections import InstrumentedList
from sqlmodel import SQLModel
from setezor.services.base_service import BaseService
from setezor.unit_of_work import UnitOfWork
from setezor.models import get_model_by_name
from setezor.repositories import SQLAlchemyRepository
from setezor.settings import COMMIT_STEP

common_semaphore = asyncio.Semaphore(1)

class DataStructureService(BaseService):
    async def make_magic(self, result: list[SQLModel], project_id: str, scan_id: str):
        self.result = result
        self.project_id = project_id
        self.scan_id = scan_id
        self.new_objects = []

        for obj in self.result:
            if hasattr(obj, "project_id"):
                obj.project_id = project_id
            if hasattr(obj, "scan_id"):
                obj.scan_id = scan_id

        async with common_semaphore:
            async with self._uow:
                for index in range(len(self.result)):
                    new_object = await self.prepare_object(self.result[index])
                    if not new_object: continue
                    await self.prepare_relationships(new_object)
                    self.new_objects.append(new_object)
                for i in range(0, len(self.new_objects), COMMIT_STEP):
                    self._uow.session.add_all(self.new_objects[i:i+COMMIT_STEP])
                    await self._uow.flush()
                await self._uow.commit()
            
    async def prepare_object(self, obj: SQLModel):
        repo: SQLAlchemyRepository = self._uow.get_repo_by_model(obj.__class__)
        existing_object = await repo.exists(obj)
        if not existing_object: # Если такого объекта нет в бд, то раскручиваем его
            return obj
        relationships: list[Relationship] = obj.__mapper__.relationships # получаем все связи
        for relationship in relationships:
            immutable_copy = getattr(obj, relationship.key) # получаем неприкосновенный экземпляр relationship
            if not immutable_copy:
                continue
            back_populates = relationship.back_populates # нашли наименование поля по которому надо обратиться к obj
            _, remote  = relationship.synchronize_pairs[0]
            if isinstance(immutable_copy, InstrumentedList):
                mutable_copy = list(immutable_copy)
                for rel_obj in mutable_copy:
                    delattr(rel_obj, back_populates)
                    setattr(rel_obj, remote.key, existing_object.id)
            else:
                self.new_objects = list(filter(lambda x: id(x) != id(immutable_copy), self.new_objects))
        return None

    async def prepare_relationships(self, obj: SQLModel):
        if obj.id:
            return
        relationships:list[RelationshipData] = self.__class__.get_relationships_with_fkeys(obj)
        for relationship in relationships:  # проходимся по всем relationship
            id_field = getattr(obj, relationship.local.name)
            if id_field:
                continue
            obj_in_relation = getattr(obj, relationship.key)
            if obj_in_relation is None: # если ссылка на родителя есть, но объект там отсутствует, 
                                        # то будем создавать
                model = self.__class__.get_table_by_name(relationship.argument) # родительская модель
                M = model(
                    project_id=self.project_id,
                    scan_id=self.scan_id
                    )
                setattr(obj, relationship.key, M) # ставим в relationship пустой объект 
                                                    # и начинаем его раскручивать
                await self.prepare_relationships(M)
                return
            
            if obj_in_relation.id:
                continue
            else: # если объект повязан, то проверяем, есть ли такой уже в базе, чтобы не создать дубликат
                repo: SQLAlchemyRepository = self._uow.get_repo_by_model(obj_in_relation.__class__)
                existing_object = await repo.exists(obj_in_relation)
                if not existing_object: # Если такого объекта нет в бд, то раскручиваем его
                    await self.prepare_relationships(obj_in_relation)
                else: # Если объект есть в бд, то манипулируем relationship
                    setattr(obj, relationship.key, existing_object)  # Проставляем найденный объект

    @classmethod
    def get_relationships_with_fkeys(cls, obj: SQLModel):
        """
            Функция получает все relationship's 
            у которых в данной модели есть ForeignKey
        """
        relationships: list[Relationship] = obj.__mapper__.relationships
        result = []
        for relationship in relationships:
            remote: Column
            local: Column
            remote, local = relationship.synchronize_pairs[0]
            # print(remote, local.name)
            if obj.__table__ != remote.table:
                result.append(RelationshipData(
                    key=relationship.key,
                    argument=relationship.argument,
                    local=local,
                    remote=remote
                ))
        return result

    @classmethod
    def get_table_by_name(cls, name: str):
        return get_model_by_name(name)


class RelationshipData:
    def __init__(self, key:str, argument:str, local:Column, remote:Column):
        self.key = key
        self.argument = argument
        self.local = local
        self.remote = remote
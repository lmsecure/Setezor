from typing import Annotated
from fastapi import Depends
from setezor.interfaces.unit_of_work import IUnitOfWork
from setezor.unit_of_work.unit_of_work import UnitOfWork

UOWDep = Annotated[IUnitOfWork, Depends(UnitOfWork)]

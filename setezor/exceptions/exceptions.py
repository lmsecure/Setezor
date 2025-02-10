from fastapi import HTTPException

class RequiresLoginException(HTTPException):
    pass

class RequiresRegistrationException(HTTPException):
    pass

class RequiresProjectException(HTTPException):
    pass

class RequiresScanException(HTTPException):
    pass
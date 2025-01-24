from fastapi import HTTPException

class RequiresLoginException(Exception):
    pass

class RequiresRegistrationException(Exception):
    pass

class RequiresProjectException(Exception):
    pass

class RequiresScanException(HTTPException):
    pass
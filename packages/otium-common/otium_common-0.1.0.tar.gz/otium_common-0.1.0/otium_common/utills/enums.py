from enum import Enum

from .exception import (
    TokenExpiredException,
    TokenValidationException
)

class TokenValidation(Enum):
    UNKNOWN = 0
    SUCCESS = 1
    INVALID = 2
    EXPIRED = 3
    FAILURE = 4
    
    def handle(self):
        if self is TokenValidation.INVALID:
            raise TokenValidationException()
        
        if self is TokenValidation.EXPIRED:
            raise TokenExpiredException()


class TokenType(Enum):
    ACCESS_TOKEN = 0
    REFRESH_TOKEN = 1

class IDType(Enum):
    USER = 0
    USER_INFO = 1
    USER_PREFERENCES = 2
    USER_PROFILE = 3
    USER_CERTIFICATION = 4
    USER_FRIEND_SHIP = 5
    USER_FOLLOW_SHIP = 6
    USER_BAN = 7
    USER_SCRAP = 8
    USER_REACTION = 9
    USER_COMMENT = 10
    USER_SUBSCRIBE = 11
    USER_PAYMENTS = 12
    USER_ESSENTIAL = 13
    USER_SETTING = 14
    USER_REVIEW = 15
    USER_TIP = 16
    USER_HISTORY = 17
    
    RECORD = 20
    RECORD_BUDGET = 21
    RECORD_ESSENTIAL = 22
    RECORD_ELEMENT = 23

    PLAN = 25
    PLAN_BUDGET = 26
    PLAN_ESSENTIAL = 27
    PLAN_ELEMENT = 28

    CONTENT = 30
    CONTENT_BUDGET = 31
    CONTENT_ESSENTIAL = 32
    CONTENT_ELEMENT = 33
    CONTENT_COMMENT = 34

    GROUP = 40
    GROUP_ESSENTIAL = 41
    GROUP_MEMBER = 42
    GROUP_SCHEDULE = 43



class ServiceResponse(Enum):
    SUCCESS = 0
    ERROR = 500
    NOT_FOUND = 404
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
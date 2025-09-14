from django.conf import settings

class  TokenConfig:
    SECRET_KEY = settings.TOKEN_SECRET_KEY
    ALGORITHM = settings.TOKEN_ALGORITHM
    ACCESS_TOKEN_EXPIRATION_TIME = int(settings.ACCESS_TOKEN_EXP_TIME)
    REFRESH_TOKEN_EXPIRATION_TIME = int(settings.REFRESH_TOKEN_EXP_TIME)
    TOKEN_AUD = settings.TOKEN_AUD
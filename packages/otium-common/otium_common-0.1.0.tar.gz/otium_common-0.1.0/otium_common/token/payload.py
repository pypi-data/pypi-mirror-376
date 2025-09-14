from django.conf import settings
from common.utills.time import get_utc_now

class PayloadBuilder:
    def __init__(self):
        self.email = None
        self.sub = None
        self.aud =  None
        self.iat = get_utc_now()
        self.exp = None
        self.iss = settings.TOKEN_ISS
        self.token_type  = None
        
    def set_type(self, token_type):
        self.token_type = token_type
        return self

    def set_sub(self, sub):
        self.sub = sub
        return self

    def set_aud(self, aud):
        self.aud = aud
        return self

    def set_iat(self, iat):
        self.iat = iat
        return self

    def set_exp(self, exp):
        self.exp = exp
        return self

    def set_iss(self, iss):
        self.iss = iss
        return self

    def set_email(self, email):
        self.email = email
        return self

    def build(self):
        return TokenPayload(self)

class TokenPayload:
    def __init__(self, payload_builder: PayloadBuilder):
        self.iss = payload_builder.iss
        self.exp = payload_builder.exp
        self.aud = payload_builder.aud
        self.iat = payload_builder.iat
        self.sub = payload_builder.sub
        self.token_type = payload_builder.token_type
        self.email = payload_builder.email

    def to_dict(self):
        return {
            "iss": self.iss,
            "exp": self.exp,
            "aud": self.aud,
            "iat": self.iat,
            "sub": self.sub,
            "type": self.token_type,
            "email": self.email,
        }

    @staticmethod
    def builder():
        return PayloadBuilder()
    
    
    
import logging

from common.token.validator import TokenValidator
from common.token.token import TokenManager

logger = logging.getLogger(__name__)
class TokenService:
    def __init__(self):
        self.token_manager = TokenManager()
        self.token_validator = TokenValidator()

    def validate(self, token):
        return self.token_validator.validate_token(token)
        
    def gen_refresh_token(self, sub, email=None):
        logging.debug(f"리프레시 토큰 생성: {sub}, email: {email}")
        return self.token_manager.generate_refresh_token(sub=sub, email=email)

    def gen_access_token(self, sub, email=None):
        logging.debug(f"액세스 토큰 생성: {sub}, email: {email}")
        return self.token_manager.generate_access_token(sub=sub, email=email)
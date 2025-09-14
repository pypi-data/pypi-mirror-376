import jwt
import logging

from common.utills.enums import (
    TokenValidation,
    TokenType
)
from common.utills.time import (
    exp_days,
    exp_hours
)
from .config import TokenConfig
from .payload import PayloadBuilder
from .validator import TokenValidator



logger = logging.getLogger(__name__)
class TokenManager:
    def __init__(self):
        self.config = TokenConfig()
        self.payload_builder = PayloadBuilder()
        self.headers = {
            'alg': self.config.ALGORITHM,
            'typ': 'JWT',
        }
        self.key = self.config.SECRET_KEY
        self.algorithm = self.config.ALGORITHM

    def generate_access_token(self, sub, email=None, aud=None):
        if aud is None:
            aud = self.config.TOKEN_AUD
        
        payload = self._build_payload(
            sub=sub,
            aud=aud,
            email=email,
            exp=exp_hours(self.config.ACCESS_TOKEN_EXPIRATION_TIME),
            token_type=TokenType.ACCESS_TOKEN.value
            )
        
        logger.debug(f"액세스 토큰 페이로드: {payload.to_dict()}")
        logger.debug(f"액세스 토큰 생성 시도: headers: {self.headers}, key: {self.key[:10]}..., alg: {self.algorithm} ...")
        return jwt.encode(
            headers=self.headers,
            payload=payload.to_dict(),
            key=self.key,
            algorithm=self.algorithm
        )

    def generate_refresh_token(self, sub, email=None, aud=None):
        if aud is None:
            aud = self.config.TOKEN_AUD
        
        payload = self._build_payload(
            sub=sub,
            aud=aud,
            email=email,
            exp=exp_days(self.config.REFRESH_TOKEN_EXPIRATION_TIME),
            token_type=TokenType.REFRESH_TOKEN.value
        )
        
        logger.debug(f"리프레시 토큰 페이로드: {payload.to_dict()}")
        logger.debug(f"리프레시 토큰 생성 시도: headers: {self.headers}, key: {self.key[:10]}..., alg: {self.algorithm} ...")
        return jwt.encode(
            headers=self.headers,
            payload=payload.to_dict(),
            key=self.key,
            algorithm=self.algorithm
        )

    def refresh_access_token(self, refresh_token, aud=None):
        if aud is None:
            aud = self.config.TOKEN_AUD
        token_validation, payload = TokenValidator().validate_token(refresh_token, aud)

        if not (token_validation == TokenValidation.SUCCESS):
            raise ValueError

        if not payload or payload.get('type') != TokenType.REFRESH_TOKEN.value:
            raise ValueError

        return self.generate_access_token(sub=payload['sub'], aud=payload['aud'])

    def _build_payload(self, sub, email, aud, exp, token_type):
        return self.payload_builder.set_sub(str(sub)).set_email(email).set_aud(aud).set_exp(exp).set_type(token_type).build()
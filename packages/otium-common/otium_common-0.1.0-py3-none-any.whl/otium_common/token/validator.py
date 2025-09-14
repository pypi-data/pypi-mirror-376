import jwt
import logging

from .config import TokenConfig
from common.utills.enums import TokenValidation

logger = logging.getLogger(__name__)
class TokenValidator:
    def validate_token(self, token, aud=None):
        if aud is None:
            aud = TokenConfig.TOKEN_AUD
            
        logger.debug(f"토큰 검증 시도: {token[:10]}..., aud: {aud}..., alg: {TokenConfig.ALGORITHM} ... secret_key: {TokenConfig.SECRET_KEY[:10]}...")
        try:
            payload = jwt.decode(
                jwt=token,
                key=TokenConfig.SECRET_KEY,
                algorithms=[TokenConfig.ALGORITHM],
                audience=aud,
            )
            logger.info(f"토큰 인증 성공: {token[:10]}")
            return TokenValidation.SUCCESS, payload
        
        except jwt.ExpiredSignatureError as e:
            logger.warning(f"토큰 만료: {token[:10]}, {e}")
            return TokenValidation.EXPIRED, None
        
        except jwt.InvalidTokenError as e:
            logger.error(f"토큰 인증 실패: {token[:10]}, {e}")
            return TokenValidation.INVALID, None
        
        except Exception as e:
            logger.error(f"예외 발생: {e}")
            raise e
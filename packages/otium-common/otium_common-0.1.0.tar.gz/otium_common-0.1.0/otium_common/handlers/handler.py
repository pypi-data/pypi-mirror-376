import logging
from functools import wraps

logger = logging.getLogger(__name__)

def handle_repo_call(success_msg: str, not_found_msg: str):
    """
    Repository 호출의 성공, 실패(None), 예외를 처리하고 로깅하는 데코레이터
    """
    def decorator(func):
        @wraps(func) # 원본 함수의 이름, docstring 등 메타데이터를 유지
        def wrapper(self, ids, *args, **kwargs):
            try:
                result = func(self, ids, *args, **kwargs)
                
                if result:
                    logger.info(f"{success_msg} : {ids}")
                    return result
                
                logger.warning(f"{not_found_msg} : {ids}")
                return None

            except Exception as e:
                logger.error(f"알 수 없는 에러 발생 : {ids}, {e}")
                return None
        return wrapper
    return decorator

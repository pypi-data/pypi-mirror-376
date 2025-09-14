import logging

from django.conf import settings
from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)
class OpenSearchRepository:
    def __init__(self):
        if settings.ENVIRONMENT != 'development':
            self.client = OpenSearch(
                hosts=[{'host': 'otium-opensearch', 'port': 9200}],
                http_auth=('admin', 'Otiumdata#2025'),  
                use_ssl=True,  
                verify_certs=False,  
                ssl_show_warn=False
            )
        else:
            self.client = None
        self.index_name = 'user'
        if self.client:
            self._create_index()
        
    
    def _create_index(self):
        if not self.client.indices.exists(index=self.index_name):
            index_body = {
                "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "dynamic": "strict",
                        "properties": {
                            "user_id": {"type": "keyword"},
                            "email": {"type": "keyword"},
                            "otium_id": {"type": "search_as_you_type"},
                            "nickname": {"type": "keyword"},
                            "profile_image": {"type": "keyword"}
                        }
                    }
                }
            }
            self.client.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Index :  '{self.index_name}' 인덱스가 성공적으로 생성됐습니다.")
        else:
            logger.info(f"Index :  '{self.index_name}' 인덱스가 이미 존재합니다.")
    
    def index_user(self, **validated_data):
        """
        유저 정보를 OpenSearch에 인덱싱합니다.
        """
        try:
            response = self.client.index(
                index=self.index_name,
                body=validated_data,
                id=str(validated_data.get('user_id'))
            )
            logger.info(f"OpenSearch에 유저 인덱싱 성공: {validated_data} |||| {response}")
        except Exception as e:
            logger.error(f"OpenSearch 인덱싱 중 오류 발생: {e}")
            raise e
        
        return response

    def update_user(self, **validated_data):
        """
        유저 정보를 OpenSearch에서 업데이트합니다.
        """
        try:
            response = self.client.update(
                index=self.index_name,
                body={"doc": validated_data},
                id=str(validated_data.get('user_id'))
            )
            logger.info(f"OpenSearch에 유저 업데이트 성공: {validated_data} |||| {response}")
            
        except Exception as e:
            logger.error(f"OpenSearch 업데이트 중 오류 발생: {e}")
            raise e
        return response

    def delete_user(self, user_id):
        """
        유저 정보를 OpenSearch에서 삭제합니다.
        """
        response = self.client.delete(
            index=self.index_name,
            id=str(user_id)
        )
        return response
    
    def search_user(self, body):
        """
        OpenSearch에서 유저 정보를 검색합니다.
        """
        try:
            logger.info(f"OpenSearch에서 유저 검색: {body}")
            response = self.client.search(
                index=self.index_name,
                body=body
            )
            return response
        
        except Exception as e:
            logger.error(f"OpenSearch 검색 중 오류 발생: {e}")
            return 500

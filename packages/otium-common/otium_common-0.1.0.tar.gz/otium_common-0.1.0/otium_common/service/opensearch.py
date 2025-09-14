from common.repository.opensearch import OpenSearchRepository

class OpenSearchService:
    def __init__(self, opensearch_repo:OpenSearchRepository):
        self.os_repo = opensearch_repo
    
    def update(self, **validated_data):
        return self.os_repo.update_user(**validated_data)
    
    def create(self, **validated_data):
        return self.os_repo.index_user(**validated_data)

    def delete(self, user_id: int):
        return self.os_repo.delete_user(user_id=user_id)
    
    def search(self, query_by_user, keyword):
        body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": keyword,
                                    "fields": [
                                        "nickname^1",         
                                        "email^2",            
                                        "otium_id^3",         
                                        "otium_id._2gram^3",
                                        "otium_id._3gram^3" 
                                    ],
                                    "type": "bool_prefix"   
                                }
                            }
                        ],
                        "must_not": {
                            "term": {
                                "user_id": query_by_user
                            }
                        },
                        "minimum_should_match": 1, 
                        "filter": [] 
                    }
                },
                "size": 10,
                "sort": [
                    {
                        "_score": {
                            "order": "desc"
                        }
                    }
                ]
            }
        return self.os_repo.search_user(body)
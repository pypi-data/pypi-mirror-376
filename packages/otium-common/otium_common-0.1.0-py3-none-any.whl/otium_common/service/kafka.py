import json
import logging

from confluent_kafka import (
    Producer,
    KafkaError
)
from django.conf import settings


logger = logging.getLogger(__name__)
class KafKaService:
    def __init__(self):
        if settings.ENVIRONMENT == 'production':
            self.host = 'kafka'
            self.broker = f'{self.host}:9092'
            self.topic = 'notification'
            conf = {
                'bootstrap.servers': self.broker,
                'acks': 'all',
                'retries': 3
            }
            self.producer = Producer(conf)

            cluster_metadata = self.producer.list_topics(timeout=10)
            if self.topic not in cluster_metadata.topics:
                logger.error(f"카프카 토픽 '{self.topic}'이(가) 존재하지 않습니다.")

    def _send_message(self, msg):
        if self.producer is None:
            logger.warning("카프카 프로듀서가 초기화되지 않았습니다. 메시지를 전송할 수 없습니다.")
            return
 
        def _delivery_report(err, msg):
            if err is not None:
                logger.error(f"카프카 메시지 전송 실패: {err}")
            else:
                logger.info(f"카프카 메시지 전송 성공: {msg.topic()} [{msg.partition()}]")

        try:
            encoded_msg = json.dumps(msg).encode('utf-8')
            self.producer.produce(self.topic, value=encoded_msg, callback=_delivery_report)
            self.producer.poll(1)

        except BufferError:
            logger.error("카프카 메시지 버퍼가 가득 찼습니다.")
            self.producer.flush()
        
        except Exception as e:
            logger.error(f"카프카 메시지 전송 중 오류 발생: {e}")
            
    def create_user(self, data):
        message = {
            "command": 'create',
            "data": data
        }
        try:
            self._send_message(message)
            return 0
        except Exception as e:
            logger.error(f"카프카 create_user 메시지 전송 중 오류 발생: {e}")
            return 500

    def delete_user(self, data):
        message = {
            "command": 'delete',
            "data": data
        }
        try:
            self._send_message(message)
            return 0
        except Exception as e:
            logger.error(f"카프카 delete_user 메시지 전송 중 오류 발생: {e}")
            return 500

    def update_user(self, data):
        message = {
            "command": 'update',
            "data": data
        }
        try:
            self._send_message(message)
            return 0
        except Exception as e:
            logger.error(f"카프카 update_user 메시지 전송 중 오류 발생: {e}")
            return 500
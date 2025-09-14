import logging
import boto3

from django.conf  import settings

logger = logging.getLogger(__name__)
class AWSService:
    def __init__(self):
        self.ses_client = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_SES_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SES_SECRET_KEY
        )
        self.sender = settings.AWS_SES_EMAIL_SENDER
        
    def send_email(self, destination, subject, body):
        try:
            response = self.ses_client.send_email(
                Source=self.sender,
                Destination={
                    "ToAddresses": [destination]
                },
                Message={
                    "Subject": {
                        "Data": subject,
                        "Charset": "UTF-8"
                    },
                    "Body": {
                        "Html": {
                            "Data": body,
                            "Charset": "UTF-8"
                        }
                    }
                }
            )
            return response
        except Exception as e:
            logging.error(f"이메일 전송 실패: {e}")
            return None
from rest_framework import serializers

class ServerErrorSerializer(serializers.Serializer):
    detail = serializers.CharField(default="서버 오류가 발생했습니다.")
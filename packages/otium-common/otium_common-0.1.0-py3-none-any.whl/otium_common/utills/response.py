from rest_framework.response import Response
from rest_framework import status

from common.serializers.response import (
    ServerErrorSerializer
)

def ok_response(data=None):
    return Response(
        data=data,
        status=status.HTTP_200_OK
    )

def create_response(data=None):
    return Response(
        data=data,
        status=status.HTTP_201_CREATED
    )

def no_content_response():
    return Response(
        status=status.HTTP_204_NO_CONTENT
    )

def not_found_response(
    data=None
    ):
    return Response(
        data=data or {"detail": "Resource not found"},
        status=status.HTTP_404_NOT_FOUND
    )

def bad_request_response(data=None):
    return Response(
        data=data,
        status=status.HTTP_400_BAD_REQUEST
    )
    
def un_auth_response(data=None):
    return Response(
        data=data,
        status=status.HTTP_401_UNAUTHORIZED
    )

def server_error_response(data=None):
    return Response(
        data=data or ServerErrorSerializer().data,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
from django.contrib.auth.backends import ModelBackend
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class PasswordlessAuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            if username is None:
                return Response({'data': 'Invalid username/password.', 'value': False}, status=status.HTTP_400_BAD_REQUEST)
            else:
                user = User.objects.get(username=username['username'])
                return Response(user)

                # if user.check_password(username['password']) is True:
                # return Response(user)
                # else:
                # return Response({'data': 'Invalid password.', 'value': False}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'data': 'Invalid username/password, Please contact your administrator', 'value': False},
                            status=status.HTTP_400_BAD_REQUEST)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

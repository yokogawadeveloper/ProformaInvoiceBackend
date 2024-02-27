from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenViewBase
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.views import APIView

import itertools, os.path, re, smtplib, numpy as np, pandas as pd
from datetime import datetime

from rest_framework import permissions
import logging
from users.models import User
from users.serializer import UserSerializer

from users.auth_backend import PasswordlessAuthBackend as pwdless
from users.user_csv_data import userDataList
from django.db.models import Q


class TokenObtainPairWithoutPasswordSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field].required = False
        self.fields['password'].required = False

    def validate(self, attrs):

        user = pwdless.authenticate(self, attrs)

        if user.status_code == 400:
            return {'data': user.data['data'], 'value': False}

        username = user.data.username
        is_active = user.data.is_active

        attrs.update({'username': username, 'password': "12345"})
        if not is_active:
            return {'data': 'Your login has been deactivated, Please contact administrator', 'value': False}
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['username'] = self.user.username
        data['is_active'] = self.user.is_active
        data['is_superuser'] = self.user.is_superuser
        data["Isadmin"] = self.user.Isadmin
        data['division'] = self.user.division
        data['category'] = self.user.category
        data['pm'] = self.user.project_manager
        data['region'] = self.user.region

        return {'data': data, 'value': True}


class Login(TokenObtainPairView):
    serializer_class = TokenObtainPairWithoutPasswordSerializer


class UsersViewSet(viewsets.ModelViewSet):
    #permission_classes = (permissions.IsAuthenticated, )
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        query_set = self.queryset.filter(is_active=True)
        return query_set

    def destroy(self, request, *args, **kwargs):
        self.get_queryset().filter(id=kwargs['pk']).update(is_active=False)
        queryset = self.get_queryset().filter(is_active=True)
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data

        _mutable = data._mutable
        data._mutable = True

        if data['DOB']:
            data['DOB'] = datetime.strptime(data['DOB'], '%Y-%m-%d').date()
            data['DOB'] = data['DOB'].strftime("%d-%m-%Y")

        _mutable = data._mutable

        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(True)

    def update(self, request, *args, **kwargs):
        data = request.data
        queries = self.queryset.filter(id=kwargs['pk']).first()
        serializer = self.serializer_class(queries, data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(True)

    def list(self, request, *args, **kwargs):
        query_params = request.query_params.dict()
        # offset = int(query_params.pop('offset', 0))
        # end = int(query_params.pop('end', 5))
        # username_list = [request.user.username, 'AnonymousUser']
        # queryset = self.get_queryset().exclude(username__in=username_list)
        queryset = self.get_queryset()
        # query_set = queryset

        total_records = queryset.filter(is_active=True).count()
        # query_set = query_set[offset:end]
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response({'records': serializer.data, 'totalRecords': total_records})


class UserBulkData(APIView):

    def post(self, request, Format=None):

        if True:
            user_list = pd.read_csv(os.path.abspath('static/inputFiles/user_data.csv'), sep='\t')

            df = pd.DataFrame(user_list)
            data = userDataList(df)

        return Response(data.data)

# By Gautam #
class GetUserList(APIView):
    def get(self, request, Format=None):
        user_list = User.objects.filter(~Q(username='admin') & Q (is_active=True)).all()
        serializer = UserSerializer(user_list, many=True)
        return Response(serializer.data)
    
    
class GetGrantSuperuserList(APIView):
    def get(self, request, Format=None):
        user_list = User.objects.filter(~Q(username='admin') & Q(is_superuser=True)).all()
        serializer = UserSerializer(user_list, many=True)
        return Response(serializer.data)


class UpdateIsSuperUser(APIView):
    def post(self, request, Format=None):
        userid = request.data.get("userId")
        is_superuser = request.data.get("is_superuser")
        
        user = User.objects.filter(id=userid).first()
        user.is_superuser = is_superuser
        user.save()
        return Response(True)
    

class updateProformaAccessForNoneSuperUser(APIView):
    def post(self, request, id ,Format=None):
        user = User.objects.filter(id=id).first()
        user.is_superuser = request.data.get("is_superuser")
        user.save()


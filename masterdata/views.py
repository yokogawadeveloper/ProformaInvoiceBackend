from rest_framework import viewsets, permissions

from rest_framework.response import Response
from .models import divisionMaster, categoryMaster, regionMaster, projectManagerMaster
from .serializer import divisionMasterSerializer, categoryMasterSerializer, regionMasterSerializer, \
    projectManagerMasterSerializer

from rest_framework.decorators import action
import datetime

# Create your views here.


class divisionMasterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = divisionMaster.objects.all()
    serializer_class = divisionMasterSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        total_records = queryset.count()
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(True)

    @action(methods=['get'], detail=False, url_path='delete/(?P<id>[0-9]+)')
    def deleteDivision(self, request, id):
        self.get_queryset().filter(DivisionId=id).update(DeleteFlag=True, DeletedBy_id=request.user.id,
                                                         DeletedOn=datetime.datetime.now())
        queryset = self.get_queryset().exclude(DeleteFlag=True)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class categoryMasterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = categoryMaster.objects.all()
    serializer_class = categoryMasterSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        total_records = queryset.count()
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(True)

    @action(methods=['get'], detail=False, url_path='delete/(?P<id>[0-9]+)')
    def deleteCategory(self, request, id):
        self.get_queryset().filter(CategoryId=id).update(DeleteFlag=True, DeletedBy_id=request.user.id,
                                                         DeletedOn=datetime.datetime.now())
        queryset = self.get_queryset().exclude(DeleteFlag=True)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class regionMasterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = regionMaster.objects.all()
    serializer_class = regionMasterSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        total_records = queryset.count()
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(True)

    @action(methods=['get'], detail=False, url_path='delete/(?P<id>[0-9]+)')
    def deleteRegion(self, request, id):
        self.get_queryset().filter(RegionId=id).update(DeleteFlag=True, DeletedBy_id=request.user.id,
                                                       DeletedOn=datetime.datetime.now())
        queryset = self.get_queryset().exclude(DeleteFlag=True)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class projectManagerMasterViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = projectManagerMaster.objects.all()
    serializer_class = projectManagerMasterSerializer

    def get_queryset(self):
        query_set = self.queryset.exclude(DeleteFlag=True)
        return query_set

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        total_records = queryset.count()
        return Response({'records': serializer.data, 'totalRecords': total_records})

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(True)

    @action(methods=['get'], detail=False, url_path='delete/(?P<id>[0-9]+)')
    def deletePM(self, request, id):
        self.get_queryset().filter(PMId=id).update(DeleteFlag=True, DeletedBy_id=request.user.id,
                                                   DeletedOn=datetime.datetime.now())
        queryset = self.get_queryset().exclude(DeleteFlag=True)
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(serializer.data)

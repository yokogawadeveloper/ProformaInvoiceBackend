from django.db import models
from users.models import User

# Create your models here.


class divisionMaster(models.Model):
    DivisionId = models.AutoField(primary_key=True, unique=True)
    DivisionName = models.CharField(max_length=100, null=True)
    BUHead = models.CharField(max_length=100, null=True)

    Abbr = models.CharField(max_length=50, null=True)

    submittedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    submittedDate = models.DateTimeField(auto_now_add=True)

    DeleteFlag = models.BooleanField(null=True)
    DeletedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    DeletedOn = models.DateTimeField(null=True)

    objects = models.Manager()


class categoryMaster(models.Model):
    CategoryId = models.AutoField(primary_key=True, unique=True)
    CategoryName = models.CharField(max_length=100, null=True)

    submittedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    submittedDate = models.DateTimeField(auto_now_add=True)

    DeleteFlag = models.BooleanField(null=True)
    DeletedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    DeletedOn = models.DateTimeField(null=True)

    objects = models.Manager()


class regionMaster(models.Model):
    RegionId = models.AutoField(primary_key=True, unique=True)
    RegionName = models.CharField(max_length=100, null=True)

    Abbr = models.CharField(max_length=50, null=True)

    submittedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    submittedDate = models.DateTimeField(auto_now_add=True)

    DeleteFlag = models.BooleanField(null=True)
    DeletedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    DeletedOn = models.DateTimeField(null=True)

    objects = models.Manager()


class projectManagerMaster(models.Model):
    PMId = models.AutoField(primary_key=True, unique=True)
    EmployeeNo = models.CharField(max_length=100, null=True)
    EmployeeName = models.CharField(max_length=100, null=True)
    BUHead = models.CharField(max_length=100, null=True)

    submittedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    submittedDate = models.DateTimeField(auto_now_add=True)

    DeleteFlag = models.BooleanField(null=True)
    DeletedBy = models.ForeignKey(User, related_name='+', null=True, on_delete=models.CASCADE)
    DeletedOn = models.DateTimeField(null=True)

    objects = models.Manager()


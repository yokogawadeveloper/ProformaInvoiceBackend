from django.db import models
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.models import UserManager


class User(AbstractUser):
    EmployeeNo = models.CharField(max_length=50, null=True)
    EmployeeName = models.CharField(max_length=50, null=True)
    Gender = models.CharField(max_length=50, null=True)
    DOB = models.DateField(null=True, blank=True)
    DeptCode = models.CharField(max_length=50, null=True)
    DeptName = models.CharField(max_length=100, null=True)
    Designation = models.CharField(max_length=100, null=True)
    Location = models.CharField(max_length=100, null=True)
    division = models.IntegerField(null=True)
    category = models.IntegerField(null=True)
    project_manager = models.IntegerField(null=True)
    region = models.IntegerField(null=True)

    CreatedAt = models.DateTimeField(auto_now_add=True)
    Delete = models.IntegerField(default=0)

    objects = UserManager()



from django.contrib.auth.models import Permission
from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    # DOB = serializers.DateField(input_formats=['%d-%m-%Y',])

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'EmployeeNo', 'EmployeeName', 'Gender',
                  'DOB', 'DeptCode', 'DeptName', 'Designation', 'Location', 'division', 'category', 'project_manager',
                  'is_superuser', 'is_active','Isadmin')

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password('12345')
        if not user.is_superuser:
            user.is_superuser = False
        user.save()
        return user

    def update(self, instance, validated_data):
        return super(UserSerializer, self).update(instance, validated_data)




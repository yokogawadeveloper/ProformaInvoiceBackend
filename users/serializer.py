from rest_framework import serializers
from users.models import User
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    # DOB = serializers.DateField(input_formats=['%d-%m-%Y',])

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'EmployeeNo', 'EmployeeName', 'Gender',
                  'DOB', 'DeptCode', 'DeptName', 'Designation', 'Location', 'division', 'category', 'project_manager',
                  'is_superuser', 'is_active')

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password('12345')
        if not user.is_superuser:
            user.is_superuser = False
        user.save()
        return user

    def update(self, instance, validated_data):
        return super(UserSerializer, self).update(instance, validated_data)
    
    def validate_password(self, value: str) -> str:
        """
        Hash value passed by user.

        :param value: password of a user
        :return: a hashed version of the password
        """

        return make_password(value)
    


        





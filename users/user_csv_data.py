from rest_framework.response import Response
from users.models import User


def userDataList(data):
    df = data.where(data.notna(), None)

    row_iter = df.iterrows()

    objs = [

        User(

            EmployeeName=row['EmployeeNo'], EmployeeNo=row['EmployeeName'], Gender=row['Sex'],
            Location=row['Location'],
            Designation=row['Designation'], DeptName=row['DeptName'], DeptCode=row['DeptCode'],
            DOB=row['dob'], username=row['LoginName'],
            password='12345', is_superuser=False, email=row['Mail'],
            is_active=True, last_login=row['mSignInDate']

        )

        for index, row in row_iter

    ]

    User.objects.bulk_create(objs)

    return Response({"value": True, "message": "File has uploaded"}, status=status.HTTP_201_CREATED)


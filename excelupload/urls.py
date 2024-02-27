from django.conf.urls import url
from .views import *


urlpatterns = [url(r'^data/$', DataCrud.as_view(), name="DataCrud")]






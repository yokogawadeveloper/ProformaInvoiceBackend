from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt import views as jwt_views
from .views import *

urlpatterns = {
    url(r'^login/', Login.as_view(), name='token_obtain_pair'),
    url(r'^login/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    # new changes
    url(r'^getuser/', GetUserList.as_view(), name='getuser'),
    url(r'^getgrantsuperuser/', GetGrantSuperuserList.as_view(), name='getnonesuperuser'),
    url(r'^updateuseraccess/', UpdateIsSuperUser.as_view(), name='updateuseraccess'),
}
urlpatterns = format_suffix_patterns(urlpatterns)

from django.urls import re_path

from .views import serve_mixed


urlpatterns = [
    re_path(r'^files/(?P<name>.+)$', serve_mixed, name='database_file')
]

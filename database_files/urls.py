from django.conf.urls import url

from .views import serve_mixed


urlpatterns = [
    url(r'^files/(?P<name>.+)$', serve_mixed, name='database_file')
]

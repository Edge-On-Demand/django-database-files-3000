from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^files/(?P<name>.+)$', views.serve_mixed, name='database_file')
]

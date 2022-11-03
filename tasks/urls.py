from django.template.defaulttags import url
from django.urls import path
from .views import index

urlpatterns = [
    path('', index, name='index'),
]

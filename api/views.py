from typing import Type

from django.db.models import Model
from django.shortcuts import render
from django.urls import path
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.serializers import ModelSerializer


# Create your views here.
# @api_view(['GET'])
# def get_data(request):
#     person = {'name': 'Dennus', 'age': 28}
#     return Response()

_GET_SUFFIX = '_get'
_POST_SUFFIX = '_post'


def generic_crud(crud_model: Type[Model]):

    # Serializer = type('Serializer', (ModelSerializer, ), {
    #     'Meta': type('Meta', (), {
    #         'model': model,
    #         'fields': '__all__'
    #     })
    # })

    class Serializer(ModelSerializer):
        class Meta:
            model = crud_model
            fields = '__all__'

    @api_view(['GET'])
    def generic_get(request):
        items = crud_model.objects.all()
        serializer = Serializer(items, many=True)
        return Response(serializer.data)

    @api_view(['POST'])
    def generic_post(request):
        serializer = Serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)

    model_name = crud_model.__name__.lower()

    get_url = f"{model_name}{_GET_SUFFIX}"
    post_url = f"{model_name}{_POST_SUFFIX}"

    return (
        path(get_url, generic_get, name=get_url),
        path(post_url, generic_post, name=post_url),
    )


def crud_overview(urls: list[path]):

    overview_dict = {
        'GET': [url.pattern._route for url in urls if url.name.endswith(_GET_SUFFIX)],
        'POST': [url.pattern._route for url in urls if url.name.endswith(_POST_SUFFIX)],
    }

    url_name = 'crud_overview'

    @api_view(['GET'])
    def overview_get(request):
        full_url = request._request.path
        url_prefix = full_url[:full_url.index(url_name)]
        # TODO Kevin: Loop urls
        return Response(overview_dict)

    # TODO Kevin: Not sure how I want to mutate the urlpatterns
    urls.append(path(url_name, overview_get, name=url_name))

""" Generic creation of CRUD based web API views """

from typing import Type

from django.db.models import Model
from django.shortcuts import render
from django.urls import path
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.serializers import ModelSerializer


_LIST_SUFFIX = '-list'
_DETAIL_SUFFIX = '-detail'
_CREATE_SUFFIX = '-create'
_UPDATE_SUFFIX = '-update'
_DELETE_SUFFIX = '-delete'


def generic_crud(crud_model: Type[Model]) -> tuple[path, path, path, path, path]:
    """
    Creates generic CRUD views for the specified model

    :param crud_model: Model to create web API CRUD operations for

    :returns: A tuple of path() instances to be inserted into your app's urlpatterns
    """

    class Serializer(ModelSerializer):
        class Meta:
            model = crud_model
            fields = '__all__'

    @api_view(['GET'])
    def generic_get_list(request: Request):
        instances = crud_model.objects.all()
        serializer = Serializer(instances, many=True)
        return Response(serializer.data)

    @api_view(['GET'])
    def generic_get_detail(request: Request, pk: int):
        instance = crud_model.objects.get(pk=pk)
        serializer = Serializer(instance, many=False)
        return Response(serializer.data)

    @api_view(['POST'])
    def generic_create(request: Request):
        serializer = Serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)

    @api_view(['POST'])
    def generic_update(request: Request, pk: int):
        instance = crud_model.objects.get(pk)
        serializer = Serializer(instance=instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)

    @api_view(['DELETE'])
    def generic_delete(request: Request, pk: int):
        crud_model.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    model_name = crud_model.__name__.lower()

    list_url = f"{model_name}{_LIST_SUFFIX}"
    detail_url = f"{model_name}{_DETAIL_SUFFIX}"
    create_url = f"{model_name}{_CREATE_SUFFIX}"
    update_url = f"{model_name}{_UPDATE_SUFFIX}"
    delete_url = f"{model_name}{_DELETE_SUFFIX}"

    return (
        path(f"{list_url}/", generic_get_list, name=list_url),
        path(f"{detail_url}/<str:pk>/", generic_get_detail, name=detail_url),
        path(f"{create_url}/", generic_create, name=create_url),
        path(f"{update_url}/<str:pk>/", generic_update, name=update_url),
        path(f"{delete_url}/<str:pk>/", generic_delete, name=delete_url),
    )


def crud_overview(urls: list[path]) -> None:
    """
    Generate a view listing web API CRUD operations.
    The new view will be appended to the provided list.

    :param urls: urlpatterns list to generate the view for.
    """

    overview_dict = {
        'LIST': [url.pattern._route for url in urls if url.name.endswith(_LIST_SUFFIX)],
        'DETAIL': [url.pattern._route for url in urls if url.name.endswith(_DETAIL_SUFFIX)],
        'CREATE': [url.pattern._route for url in urls if url.name.endswith(_CREATE_SUFFIX)],
        'UPDATE': [url.pattern._route for url in urls if url.name.endswith(_UPDATE_SUFFIX)],
        'DELETE': [url.pattern._route for url in urls if url.name.endswith(_DELETE_SUFFIX)],
    }

    url_name = 'crud_overview'

    @api_view(['GET'])
    def overview_get(request):
        """ Mutate the overview dictionary with absolute URLs """

        # Show absolute URLs for the web API
        full_url = request._request.path
        url_prefix = full_url[:full_url.index(url_name)]
        abs_url_dict = {key: [f"{url_prefix}{url}" for url in urls] for key, urls in overview_dict.items()}
        return Response(abs_url_dict)

    # TODO Kevin: Not sure how I want to mutate the urlpatterns
    urls.append(path(url_name, overview_get, name=url_name))

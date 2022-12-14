""" Generic creation of CRUD based web API views """



from enum import Enum
from itertools import chain
from django.urls import path
from typing import Type, Iterable
from rest_framework import status
from django.shortcuts import render
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework.serializers import ModelSerializer, ListSerializer
from django.db.models import Model, QuerySet, ForeignKey
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor, ReverseOneToOneDescriptor, \
    ManyToManyDescriptor

_LIST_SUFFIX = '-list'
_DETAIL_SUFFIX = '-detail'
_CREATE_SUFFIX = '-create'
_UPDATE_SUFFIX = '-update'
_DELETE_SUFFIX = '-delete'
_INSPECT_SUFFIX = '-inspect'

_DEFAULT_DEPTH = 2  # Default serialization depth.
_MAXIMUM_DEPTH = 10
assert _DEFAULT_DEPTH < _MAXIMUM_DEPTH


def generic_serializer(crud_model: Type[Model], depth_limit: int = 0, field_exclude: Iterable[str] = ()) -> Type[WritableNestedModelSerializer]:
    """
    Creates a Generic recursive ModelSerializer for the provided model

    :param crud_model: Model subclass for which a serializer should be created.
    :param depth_limit: Maximum relation depth, below which objects won't be nested.
    :param field_exclude: List of field names to be excluded from serialization.

    :returns: The new ModelSerializer class.
    """

    if depth_limit > 0:  # We may create serializers for related sets...
        # Generate a dictionary where keys are foreign key fields or related set field names, and values are serializers
        related_sets: dict[str, Type[ModelSerializer]] = {  # Serialize related sets, and disallow the related model from going back through the ForeignKey
            rel.related_name: generic_serializer(rel.related_model, depth_limit-1, {rel.remote_field.name})(many=True)
            # TODO Kevin: Not sure why we get a related set with None name
            for rel in crud_model._meta.related_objects if rel.name not in field_exclude and rel.related_name is not None
        } | {  # Serialize ForeignKey, and disallow the related model from going back through the related set
            field.name: generic_serializer(field.related_model, depth_limit-1, {field.remote_field.name})(many=False)
            for field in crud_model._meta.fields if isinstance(field, ForeignKey) and field.name not in field_exclude
        }
    else:
        related_sets = {}

    # TODO Kevin: Updating the cards of a cardlist will delete cards that are absent from the received JSON.
    #   This is probably not desired.

    def to_internal_value(self: WritableNestedModelSerializer, data: dict):
        assert isinstance(data, dict)
        for fieldname, fieldvalue in data.items():
            if isinstance(fieldvalue, (int, list)) and isinstance(serfield := self.fields[fieldname], ModelSerializer):
                if isinstance(serfield, ListSerializer):  # TODO Kevin: Haven't tested if checking on ListSerializer works
                    data[fieldname] = type(serfield)(serfield.Meta.model.objects.filter(pk__in=fieldvalue), many=True).data
                else:
                    data[fieldname] = type(serfield)(serfield.Meta.model.objects.get(pk=fieldvalue), many=False).data
        return super(WritableNestedModelSerializer, self).to_internal_value(data)

    # Create the class using the 'type' function, to allow setting custom serializers for related sets
    GenericSerializer = type('GenericSerializer', (WritableNestedModelSerializer,), {
        **related_sets,
        'to_internal_value': to_internal_value,
        'Meta': type('Meta', (), {
            "model": crud_model,
            # TODO kevin: hasattr() is a bit of a dirty fix
            "fields": [field.name for field in chain(crud_model._meta.fields, crud_model._meta.related_objects) if field.name not in field_exclude and hasattr(crud_model, field.name)],
            "depth": depth_limit if related_sets else 0,  # We basically ignore depth, when we generate the classes ourselves ¯\_(ツ)_/¯
        })
    })

    return GenericSerializer


class CrudOps(Enum):
    CREATE = 0
    LIST = 1
    DETAIL = 2
    UPDATE = 3
    DELETE = 4
    MODEL = 5


def generic_crud(crud_model: Type[Model], exclude: Iterable[CrudOps] = None) -> Iterable[path]:
    """
    Creates generic CRUD views for the specified model

    :param crud_model: Model to create web API CRUD operations for
    :param exclude: CRUD operations to exclude.

    :returns: A tuple of path() instances to be inserted into your app's urlpatterns
    """

    generic_serializers = {_DEFAULT_DEPTH: generic_serializer(crud_model, _DEFAULT_DEPTH)}

    def _get_or_create_serializer(request: Request) -> Type[ModelSerializer]:
        """ Create a new serializer class for the specified depth if required. """

        try:
            depth = int(request.GET.get('depth', _DEFAULT_DEPTH))
            if depth > _MAXIMUM_DEPTH:
                depth = _MAXIMUM_DEPTH
        except ValueError:
            depth = _DEFAULT_DEPTH

        if depth not in generic_serializers:
            generic_serializers[depth] = generic_serializer(crud_model, depth)
        return generic_serializers[depth]

    @api_view(['GET'])
    def generic_get_list(request: Request):
        instances = crud_model.objects.all()
        serializer = _get_or_create_serializer(request)(instances, many=True)
        return Response(serializer.data)

    @api_view(['GET'])
    def generic_get_detail(request: Request, pk: int):
        instance = crud_model.objects.get(pk=pk)
        serializer = _get_or_create_serializer(request)(instance, many=False)
        return Response(serializer.data)

    @api_view(['POST'])
    def generic_create(request: Request):
        serializer = _get_or_create_serializer(request)(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data)

    @api_view(['POST'])
    def generic_update(request: Request, pk: int):
        instance = crud_model.objects.get(pk=pk)
        serializer = _get_or_create_serializer(request)(instance=instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data)

    @api_view(['DELETE'])
    def generic_delete(request: Request, pk: int):
        crud_model.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @api_view(['GET'])
    def generic_inspect(request: Request):
        fieldlist_json = {
            field.name: {'type': str(field.description),
                         'isRequired': False if field.null or field.blank else True,
                         'primaryKey': field.primary_key}
            for field in crud_model._meta.fields
        }
        return Response(fieldlist_json)

    model_name = crud_model.__name__.lower()

    list_url = f"{model_name}{_LIST_SUFFIX}"
    detail_url = f"{model_name}{_DETAIL_SUFFIX}"
    create_url = f"{model_name}{_CREATE_SUFFIX}"
    update_url = f"{model_name}{_UPDATE_SUFFIX}"
    delete_url = f"{model_name}{_DELETE_SUFFIX}"
    model_url = f"{model_name}"  # Inspect model structure.

    operations: list[path] = []
    if exclude is None or CrudOps.LIST not in exclude:
        operations.append(path(f"{list_url}/", generic_get_list, name=f"api-{list_url}"))
    if exclude is None or CrudOps.DETAIL not in exclude:
        operations.append(path(f"{detail_url}/<str:pk>/", generic_get_detail, name=f"api-{detail_url}"))
    if exclude is None or CrudOps.CREATE not in exclude:
        operations.append(path(f"{create_url}/", generic_create, name=f"api-{create_url}"))
    if exclude is None or CrudOps.UPDATE not in exclude:
        operations.append(path(f"{update_url}/<str:pk>/", generic_update, name=f"api-{update_url}"))
    if exclude is None or CrudOps.DELETE not in exclude:
        operations.append(path(f"{delete_url}/<str:pk>/", generic_delete, name=f"api-{delete_url}"))
    if exclude is None or CrudOps.MODEL not in exclude:
        operations.append(path(f"{model_url}/", generic_inspect, name=f"api-{model_url}-inspect"))

    return operations


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
        'MODEL': [url.pattern._route for url in urls if url.name.endswith(_INSPECT_SUFFIX)]
    }
    # overview_dict['OTHER'] = [url.pattern._route for url in urls if url.pattern._route not in set(chain(overview_dict.values()))]

    url_name = 'crud-overview'

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

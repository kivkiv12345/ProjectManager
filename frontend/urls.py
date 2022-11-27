"""
The following code will automatically generate urls and classes for ListViews for all apps and models.

To override view classes; create a class in frontend/views.py, where:
'GenericAppModelList' classes are named as 'app_label'View (ex: ContosoUniversityView),
and 'GenericListView' classes are named as 'object_name'ListView (ex: InstructorListView).
"""

import sys
from typing import Type
from django.apps import apps
from django.urls import path
from django.contrib import admin
from django.db.models import Model
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView

from frontend.views import GenericListView, GenericCreateView, GenericUpdateView, GenericDeleteView, GenericForm, \
    GenericAppModelList


# Manually added URLs go here
urlpatterns = [
    # Redirect index to the Contoso University frontend administration page
    path('', RedirectView.as_view(url='contoso_university', permanent=False), name='index')
]

# Exclude apps from automatic url generation here.
applist: list[str] = [app for app in apps.app_configs.keys() if app not in {
    'crispy_forms', 'nested_inline', 'staticfiles', 'thumbnail', 'admin',
    'django_tables2', 'contenttypes', 'sessions', 'messages', 'humanize',
    'rest_framework', 'django_extensions',
}]

# TODO Kevin URLs: Perhaps allow for providing a list, by using 'next()'
# Describes which module override classes are located in.
# Set to: __name__, if you would prefer to place them in this module.
OVERRIDE_MODULE = 'frontend.views'

for app in applist:
    try:

        try:  # To get and override class for the app model list.
            AppViewClass: Type[GenericAppModelList] = getattr(sys.modules[OVERRIDE_MODULE], f"{app.title()}View")
        except AttributeError:  # Create a generic class ourselves if an override doesn't exist.
            class AppViewClass(GenericAppModelList):
                current_app = str(app)

        urlpatterns.append(path(f"{app}/", AppViewClass.as_view(), name=app))

        for model in apps.get_app_config(app).get_models():
            if model in admin.site._registry:  # We depend on the settings specified for the ModelAdmin

                # We need a lot of these later
                model_name: str = model._meta.model_name
                object_name: str = model._meta.object_name
                model_frontend_url = f"{app}/{model_name}"  # Where are the views for this app located.


                def get_or_create_form_class() -> Type[GenericForm]:
                    """ Create or find a form class for the current model """

                    form_class_name = f"{object_name}Form"

                    try:
                        return getattr(sys.modules[OVERRIDE_MODULE], form_class_name)
                    except AttributeError:
                        class FormClass(GenericForm):
                            model = model

                            class Meta:
                                model = model
                                exclude = ()

                        FormClass.__name__ = form_class_name

                        return FormClass


                # Find or create views for the current model

                listview_class_name = f"{object_name}ListView"
                try:
                    ListViewClass: Type[GenericListView] = getattr(sys.modules[OVERRIDE_MODULE], listview_class_name)
                except AttributeError:
                    class ListViewClass(GenericListView):
                        model = model
                    ListViewClass.__name__ = listview_class_name
                assert issubclass(ListViewClass, GenericListView)

                createview_class_name = f"{object_name}Create"
                try:
                    CreateViewClass: Type[GenericCreateView] = getattr(sys.modules[OVERRIDE_MODULE], createview_class_name)
                except AttributeError:
                    class CreateViewClass(GenericCreateView):
                        model = model
                        form_class = get_or_create_form_class()
                    CreateViewClass.__name__ = createview_class_name
                assert issubclass(CreateViewClass, GenericCreateView)

                updateview_class_name = f"{object_name}Update"
                try:
                    UpdateViewClass: Type[GenericUpdateView] = getattr(sys.modules[OVERRIDE_MODULE], updateview_class_name)
                except AttributeError:
                    class UpdateViewClass(GenericUpdateView):
                        model = model
                        form_class = get_or_create_form_class()
                    UpdateViewClass.__name__ = updateview_class_name
                assert issubclass(UpdateViewClass, GenericUpdateView)

                deleteview_class_name = f"{object_name}Delete"
                try:
                    DeleteViewClass: Type[GenericDeleteView] = getattr(sys.modules[OVERRIDE_MODULE], deleteview_class_name)
                except AttributeError:
                    class DeleteViewClass(GenericDeleteView):
                        model = model
                    DeleteViewClass.__name__ = deleteview_class_name
                assert issubclass(DeleteViewClass, GenericDeleteView)

                urlpatterns += (
                    path(f"{model_frontend_url}/", never_cache(ListViewClass.as_view()), name=model_name),
                    path(f"{model_frontend_url}/add/", CreateViewClass.as_view(), name=f"{model_name}-create"),
                    path(f"{model_frontend_url}/<int:pk>/change", UpdateViewClass.as_view(), name=f"{model_name}-update"),
                    path(f"{model_frontend_url}/<int:pk>/delete", DeleteViewClass.as_view(), name=f'{model_name}-delete'),
                )
    except AttributeError:
        print(f"app: '{app}', is improperly configured for automatic URL and view generation")
        # Contact your nearest Kevin, if you have questions about this error.

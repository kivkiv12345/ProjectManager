from django.urls import path

from .views import generic_crud, crud_overview
from contoso_university.models import Student, Enrollment, Instructor

urlpatterns = [
    *generic_crud(Student),
    *generic_crud(Enrollment),
    *generic_crud(Instructor),

]

crud_overview(urlpatterns)

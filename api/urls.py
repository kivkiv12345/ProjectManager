from django.urls import path

from .views import generic_crud, crud_overview
from contoso_university.models import Student, Enrollment, Instructor, Course, Curriculum
from tasks.models import Task, Todo, Worker, Team

urlpatterns = [
    *generic_crud(Student),
    *generic_crud(Enrollment),
    *generic_crud(Course),
    *generic_crud(Curriculum),
    *generic_crud(Instructor),

    *generic_crud(Task),
    *generic_crud(Todo),
    *generic_crud(Worker),
    *generic_crud(Team),

]

crud_overview(urlpatterns)

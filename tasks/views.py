from django.shortcuts import render
from .models import Task, Todo
from django.db.models import Prefetch


# Create your views here.
def seed_tasks():
    """ Add some data to the database. """

    # Create software task.
    # Task.objects.create() creates the Task immediately.
    # It also allows us to set initial values.
    software_task = Task.objects.create(name="Produce software")
    # The task is already created, so we can use it as a foreign key
    Todo.objects.create(task=software_task, title="Write code")
    Todo.objects.create(task=software_task, title="Compile source")
    Todo.objects.create(task=software_task, title="Test program")

    task = Task.objects.create(name="Brew coffee")
    Todo.objects.create(task=task, title="Pour water")
    Todo.objects.create(task=task, title="Pour coffee")
    Todo.objects.create(task=task, title="Turn on")


def print_incomplete_tasks_and_todos():

    for task in Task.objects.filter(todos__complete=False).distinct().prefetch_related(Prefetch('todos', to_attr='pre_todos')):
        print(task)
        for todo in task.pre_todos:
            if not todo.complete:
                print(todo)

from django.shortcuts import render
from .models import Task, Todo


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

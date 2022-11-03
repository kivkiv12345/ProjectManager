from django.shortcuts import render
from .models import Task, Todo, Worker, Team
from django.db.models import Prefetch, QuerySet


# Create your views here.
def index(request):
    return render(request, 'tasks/index.html', {})

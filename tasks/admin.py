from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin

from .models import Task, Todo, Worker, Team, User, Groupuser, Notgroup


class TodoInlines(admin.TabularInline):
    model = Todo
    extra = 0


class TaskAdmin(ModelAdmin):
    inlines = [TodoInlines]


# Register your models here.
admin.site.register(Task, TaskAdmin)
admin.site.register(Todo)


admin.site.register(Team)
admin.site.register(Worker)


# From inspection
admin.site.register(User)
admin.site.register(Notgroup)
admin.site.register(Groupuser)

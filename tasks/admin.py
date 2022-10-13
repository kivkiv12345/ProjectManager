from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import InlineModelAdmin

from .models import Task, Todo


class TodoInlines(admin.TabularInline):
    model = Todo
    extra = 0


class TaskAdmin(ModelAdmin):
    inlines = [TodoInlines]


# Register your models here.
admin.site.register(Task, TaskAdmin)
admin.site.register(Todo)

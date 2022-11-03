from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.admin.options import InlineModelAdmin

from .models import Instructor, OfficeAssignment, Course, Department, Enrollment, Student


class DepartmentInlines(TabularInline):
    model = Department
    extra = 0


class InstructorAdmin(ModelAdmin):
    inlines = [DepartmentInlines]


class EnrollmentInlines(TabularInline):
    model = Enrollment
    extra = 0


class StudentAdmin(ModelAdmin):
    inlines = [EnrollmentInlines]


# Register your models here.
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Department)
admin.site.register(OfficeAssignment)


admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Student, StudentAdmin)

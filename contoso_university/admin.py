
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Instructor, OfficeAssignment, Course, Curriculum, Enrollment, Student, Team, TeamCourse


class EnrollmentInlines(TabularInline):
    model = Enrollment
    extra = 0


class StudentAdmin(ModelAdmin):
    inlines = [EnrollmentInlines]


class TeamCourseInlines(TabularInline):
    model = TeamCourse
    extra = 0
    verbose_name = 'course'


class TeamAdmin(ModelAdmin):
    inlines = [TeamCourseInlines]


# Register your models here.
admin.site.register(Instructor)
admin.site.register(Curriculum)
admin.site.register(OfficeAssignment)


admin.site.register(Team, TeamAdmin)
#admin.site.register(TeamCourse)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Student, StudentAdmin)

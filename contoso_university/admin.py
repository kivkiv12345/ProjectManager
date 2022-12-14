
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin import ModelAdmin, TabularInline
from .models import Instructor, OfficeAssignment, Course, Curriculum, Enrollment, Student, Team, TeamCourse


class EnrollmentInline(TabularInline):
    model = Enrollment
    extra = 0


class StudentAdmin(ModelAdmin):
    inlines = [EnrollmentInline]
    list_filter = ('current_team',)  # list_filter doesn't seem to show up for some reason :/
    search_fields = ('first_name', 'last_name', )


class TeamCourseInline(TabularInline):
    model = TeamCourse
    extra = 0
    verbose_name = 'course'


class StudentInline(TabularInline):
    model = Student
    extra = 0


class TeamAdmin(ModelAdmin):
    inlines = (TeamCourseInline, StudentInline,)


class InstructorAdmin(ModelAdmin):
    model = Instructor
    filter_horizontal = ('team_courses',)
    list_display = ('first_name', 'office_assignment', )
    search_fields = ('first_name', 'last_name',)
    list_filter = ('team_courses',)


# Register your models here.
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Curriculum)
admin.site.register(OfficeAssignment)


admin.site.register(Team, TeamAdmin)
#admin.site.register(TeamCourse)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Student, StudentAdmin)

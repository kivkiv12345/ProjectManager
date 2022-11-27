from django.db.models import Model, OneToOneField, SET_NULL, ManyToManyField, ForeignKey, SmallIntegerField, CASCADE, \
    CharField, FloatField, DateField, Manager, QuerySet


# Create your models here.
class Person(Model):
    first_name = CharField(max_length=128)
    last_name = CharField(max_length=128)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.first_name} [{type(self).__name__}]"


class Curriculum(Model):
    name = CharField(max_length=128)
    budget = FloatField()
    start_date = DateField()

    def __str__(self):
        return self.name


class CourseManager(Manager):
    """ Selects related team by default, so we can display their name. """

    def get_queryset(self) -> QuerySet['Course']:
        return super(CourseManager, self).select_related('team')


class Course(Model):
    title = CharField(max_length=128)
    credits = SmallIntegerField()

    objects = CourseManager

    def __str__(self):
        return f"{self.title}"


class Team(Model):
    name = CharField(max_length=128)
    curriculum = ForeignKey(Curriculum, on_delete=CASCADE, null=True, blank=True, related_name='teams')
    courses = ManyToManyField(Course, through='TeamCourse')

    def __str__(self):
        return self.name


class TeamCourseManager(Manager):
    """ Selects related team by default, so we can display their name. """

    def get_queryset(self) -> QuerySet['TeamCourseManager']:
        return super(TeamCourseManager, self).select_related('team', 'course')


class TeamCourse(Model):
    """ Represents a specific team's enrollment into a course. """

    course = ForeignKey(Course, on_delete=CASCADE)
    team = ForeignKey(Team, on_delete=CASCADE)

    objects = TeamCourseManager

    class Meta:
        unique_together = ['course', 'team']

    def __str__(self):
        return f"{self.course.title} | {self.team.name}"


class Instructor(Person):
    hire_date = DateField(auto_now_add=True)
    team_courses = ManyToManyField(TeamCourse, blank=True)


class OfficeAssignmentManager(Manager):
    """ Selects related course and student by default, so we can display their names. """

    def get_queryset(self) -> QuerySet['OfficeAssignment']:
        return super(OfficeAssignmentManager, self).select_related('instructor')


class OfficeAssignment(Model):
    location = CharField(max_length=128)
    instructor = OneToOneField(Instructor, on_delete=CASCADE, primary_key=True, related_name='office_assignment')

    objects = OfficeAssignmentManager

    def __str__(self):
        return f"{self.location} | {self.instructor}"


class Student(Person):
    enrollment_date = DateField()
    team_courses = ManyToManyField(TeamCourse, through='Enrollment')
    current_team = ForeignKey(Team, on_delete=CASCADE, related_name='students')


class EnrollmentManager(Manager):
    """ Selects related course and student by default, so we can display their names. """

    def get_queryset(self) -> QuerySet['Enrollment']:
        return super(EnrollmentManager, self).select_related('course', 'student')


class Enrollment(Model):
    """ Represents a specific student's enrollment into a course """

    team_course = ForeignKey(TeamCourse, on_delete=CASCADE, related_name='enrollments')
    student = ForeignKey(Student, on_delete=CASCADE, related_name='enrollments')
    grade = SmallIntegerField(null=True, blank=True)

    objects = EnrollmentManager

    class Meta:
        unique_together = ['team_course', 'student']  # Prevent students from having the same course multiple times.

    def __str__(self):
        return f"{self.student.first_name} - {self.team_course.course.title} | [{self.grade or '-'}]"



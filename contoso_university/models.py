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


class Department(Model):
    name = CharField(max_length=128)
    budget = FloatField()
    start_date = DateField()
    instructor = ForeignKey('Instructor', on_delete=SET_NULL, null=True)

    def __str__(self):
        return self.name


class Course(Model):
    title = CharField(max_length=128)
    credits = SmallIntegerField()
    department = ForeignKey(Department, on_delete=CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.title} [{self.credits}]"


class Instructor(Person):
    hire_date = DateField(auto_now_add=True)
    courses = ManyToManyField(Course, null=True, blank=True)


class OfficeAssignment(Model):
    location = CharField(max_length=128)
    instructor = OneToOneField(Instructor, on_delete=CASCADE)


class Student(Person):
    enrollment_date = DateField()


class EnrollmentManager(Manager):
    """ Selects related course and student by default, so we can display their names. """

    def get_queryset(self) -> QuerySet['Enrollment']:
        return super(EnrollmentManager, self).select_related('course', 'student')


class Enrollment(Model):
    course = ForeignKey(Course, on_delete=CASCADE)
    student = ForeignKey(Student, on_delete=CASCADE)
    grade = SmallIntegerField(null=True, blank=True)

    objects = EnrollmentManager

    class Meta:
        unique_together = ['course', 'student']  # Prevent students from having the same course multiple times.

    def __str__(self):
        return f"{self.student.first_name} - {self.course.title} | [{self.grade or '-'}]"



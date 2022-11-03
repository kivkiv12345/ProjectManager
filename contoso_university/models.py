from django.db.models import Model, OneToOneField, SET_NULL, ManyToManyField, ForeignKey, SmallIntegerField, CASCADE, \
    CharField, FloatField, DateField


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


class Course(Model):
    title = CharField(max_length=128)
    credits = SmallIntegerField()
    department = ForeignKey(Department, on_delete=CASCADE)


class Instructor(Person):

    hire_date = DateField(auto_now_add=True)
    courses = ManyToManyField(Course)


class OfficeAssignment(Model):
    location = CharField(max_length=128)
    instructor = OneToOneField(Instructor, on_delete=CASCADE)


class Student(Person):
    enrollment_date = DateField()


class Enrollment(Model):
    course = ForeignKey(Course, on_delete=CASCADE)
    student = ForeignKey(Student, on_delete=CASCADE)
    grade = SmallIntegerField()

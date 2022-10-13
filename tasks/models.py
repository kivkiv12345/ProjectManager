from django.db.models import Model, IntegerField, CharField, ForeignKey, BooleanField, CASCADE


class Task(Model):
    name = CharField(max_length=256, blank=False)


class Todo(Model):
    title = CharField(max_length=256, blank=False)
    complete = BooleanField(default=False)
    task = ForeignKey(Task, on_delete=CASCADE)

from django.db.models import Model, IntegerField, CharField, ForeignKey, BooleanField, CASCADE


class Task(Model):
    name = CharField(max_length=256, blank=False)

    def __str__(self):
        return self.name


class Todo(Model):
    title = CharField(max_length=256, blank=False)
    complete = BooleanField(default=False)
    task = ForeignKey(Task, on_delete=CASCADE)

    def __str__(self):
        return self.title + f" [{'X' if self.complete else ' '}]"



from django.db.models import Model, IntegerField, CharField, ForeignKey, BooleanField, CASCADE, ManyToManyField, SET_NULL


class Task(Model):
    name = CharField(max_length=256, blank=False)

    def __str__(self):
        return self.name


class Todo(Model):
    title = CharField(max_length=256, blank=False)
    complete = BooleanField(default=False)
    task = ForeignKey(Task, on_delete=CASCADE, related_name='todos')

    def __str__(self):
        return self.title + f" [{'X' if self.complete else ' '}]"


class Worker(Model):
    name = CharField(max_length=256)
    todo = ForeignKey(Todo, on_delete=SET_NULL, null=True, related_name='workers')

    def __str__(self):
        return self.name


class Team(Model):
    name = CharField(max_length=256)
    workers = ManyToManyField(Worker, related_name='workers')
    current_task = ForeignKey(Task, on_delete=SET_NULL, null=True, related_name='tasks')

    def __str__(self):
        return self.name



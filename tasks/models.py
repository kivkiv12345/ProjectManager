from django.db.models import Model, IntegerField, CharField, ForeignKey, BooleanField, CASCADE, ManyToManyField, \
    SET_NULL, AutoField


class Task(Model):
    name = CharField(max_length=256, blank=False)
    team = ForeignKey('Team', on_delete=SET_NULL, null=True, related_name='tasks')  # assigned_to

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
    workers = ManyToManyField(Worker, related_name='teams')
    current_task = ForeignKey(Task, on_delete=SET_NULL, null=True, related_name='teams')

    def __str__(self):
        return self.name


# *********** Inspected Models ***********
class Groupuser(Model):
    groupid = ForeignKey('Notgroup', on_delete=CASCADE, db_column='GroupId', primary_key=True, unique=False)  # Field name made lowercase.
    userid = ForeignKey('User', on_delete=CASCADE, db_column='UserId', blank=True, null=True, unique=False)  # Field name made lowercase.

    class Meta:
        db_table = 'GroupUser'
        unique_together = ['groupid', 'userid']


class Notgroup(Model):
    groupid = AutoField(db_column='GroupId', primary_key=True)  # Field name made lowercase.
    name = CharField(db_column='Name', blank=True, null=True, max_length=32)  # Field name made lowercase.

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'NotGroup'


class User(Model):
    userid = AutoField(db_column='UserId', primary_key=True)  # Field name made lowercase.
    username = CharField(db_column='Username', blank=True, null=True, max_length=32)  # Field name made lowercase.
    password = CharField(db_column='Password', blank=True, null=True, max_length=36)  # Field name made lowercase.

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'User'


""" Here be the functions the tasks require us to create. """

from django.db.models import QuerySet, Prefetch
from tasks.models import Task, Todo, Team, Worker


def seed_tasks():
    """ Add tasks and todos to the database. """

    # Create software task.
    # Task.objects.create() creates the Task immediately.
    # It also allows us to set initial values.
    software_task = Task.objects.get_or_create(name="Produce software")[0]
    # The task is already created, so we can use it as a foreign key
    Todo.objects.get_or_create(task=software_task, title="Write code")
    Todo.objects.get_or_create(task=software_task, title="Compile source")
    Todo.objects.get_or_create(task=software_task, title="Test program")

    task = Task.objects.get_or_create(name="Brew coffee")[0]
    Todo.objects.get_or_create(task=task, title="Pour water")
    Todo.objects.get_or_create(task=task, title="Pour coffee")
    Todo.objects.get_or_create(task=task, title="Turn on")


def seed_workers():
    """ Add teams and workers to the database. """

    # Add teams first, so we can add workers to them afterwards.
    # Using Team.workers.add() allows us to add a Worker to the many-to-many relationship.
    # .get_or_create() will only create a row if a matching one doesn't exist.

    frontend_team = Team.objects.get_or_create(name='Frontend')[0]
    frontend_team.workers.add(
        Worker.objects.get_or_create(name='Steen Secher')[0],
        Worker.objects.get_or_create(name='Ejvind Møller')[0],
        Worker.objects.get_or_create(name='Konrad Sommer')[0]
    )

    backend_team = Team.objects.get_or_create(name='Backend')[0]
    backend_team.workers.add(
        Worker.objects.get_or_create(name='Konrad Sommer')[0],
        Worker.objects.get_or_create(name='Sofus Lotus')[0],
        Worker.objects.get_or_create(name='Remo Lademann')[0]
    )

    tester_team = Team.objects.get_or_create(name='Testere')[0]
    tester_team.workers.add(
        Worker.objects.get_or_create(name='Ella Fanth')[0],
        Worker.objects.get_or_create(name='Anne Dam')[0],
        Worker.objects.get_or_create(name='Steen Secher')[0]
    )


def print_incomplete_tasks_and_todos(do_print=True):

    query = Task.objects.filter(todos__complete=False).distinct().prefetch_related(Prefetch('todos', to_attr='pre_todos'))

    # Prefetch tasks related todos, so we only perform a 'single' query.
    # Task.objects.filter(todos__complete=False) Means there must be an uncompleted todo.
    if do_print:
        for task in query:
            print(task)
            for todo in task.pre_todos:
                if not todo.complete:
                    print(todo)

    return query


def print_teams_without_tasks(do_print=False) -> QuerySet[Team]:
    """
    :param do_print: Print the contents of the query, this will cause it to be evaluated.
    :return: A Queryset of teams with any tasks.
    """

    query = Team.objects.filter(tasks__isnull=True, current_task__isnull=True)

    # We cannot print the query without evaluating it, this makes it impossible to modify it further.
    if do_print:
        for team in query:
           print(team)

    return query


def print_team_current_task(do_print=True):

    # query = Task.objects.all().select_related('team').values('team__name', 'name')
    #
    # if do_print:
    #     for task_dict in query:
    #         print(f"{task_dict['team__name']}\t{task_dict['name']}")

    # It's possible to use Team.objects.all().values() to only select some columns,
    # but that doesn't seem to work with .prefetch_related().
    query = Team.objects.all().prefetch_related(Prefetch('tasks', to_attr='pre_tasks'))

    if do_print:
        for team in query:
            print('--\t' + team.name)
            for task in team.pre_tasks:
                print('\t' + str(task))

    return query


def hook_init():
    """ Will run once when Django starts """

    print_team_current_task()

# Generated by Django 4.1.2 on 2022-10-13 12:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_worker_alter_todo_task_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='current_task',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='tasks.task'),
        ),
        migrations.AddField(
            model_name='worker',
            name='todo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='workers', to='tasks.todo'),
        ),
    ]

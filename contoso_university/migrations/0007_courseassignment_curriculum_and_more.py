# Generated by Django 4.1.2 on 2022-11-14 10:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contoso_university', '0006_remove_course_department_student_courses_team_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contoso_university.course')),
            ],
        ),
        migrations.CreateModel(
            name='Curriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('budget', models.FloatField()),
                ('start_date', models.DateField()),
            ],
        ),
        migrations.RemoveField(
            model_name='instructor',
            name='courses',
        ),
        migrations.RemoveField(
            model_name='team',
            name='department',
        ),
        migrations.DeleteModel(
            name='Department',
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='curriculum',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contoso_university.curriculum'),
        ),
        migrations.AddField(
            model_name='courseassignment',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contoso_university.instructor'),
        ),
    ]
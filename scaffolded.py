""" Raw output from Django DB inspection of scaffolding.sqlite3 """

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Groupuser(models.Model):
    groupid = models.OneToOneField('Notgroup', on_delete=models.DO_NOTHING, db_column='GroupId', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('User', on_delete=models.DO_NOTHING, db_column='UserId', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'GroupUser'
        unique_together = ['groupid', 'userid']


class Notgroup(models.Model):
    groupid = models.AutoField(db_column='GroupId', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(db_column='Name', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'NotGroup'


class User(models.Model):
    userid = models.AutoField(db_column='UserId', primary_key=True, blank=True, null=True)  # Field name made lowercase.
    username = models.CharField(db_column='Username', blank=True, null=True)  # Field name made lowercase.
    password = models.CharField(db_column='Password', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'User'

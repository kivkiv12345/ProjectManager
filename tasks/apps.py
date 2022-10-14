from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        import os
        from .funcs import hook_init
        if os.environ.get('RUN_MAIN'):
            hook_init()

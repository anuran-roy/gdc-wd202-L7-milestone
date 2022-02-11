from django.contrib import admin

# Register your models here.

from tasks.models import Task, Changelog

admin.sites.site.register(Task)
admin.sites.site.register(Changelog)

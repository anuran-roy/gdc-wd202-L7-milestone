from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.core.validators import MinValueValidator

from django.contrib.auth.models import User
import json

STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)


class Task(models.Model):
    title = models.CharField(max_length=100)
    # priority = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )

    def __str__(self):
        return self.title


class Changelog(models.Model):
    diff = models.TextField(null=True, blank=True)
    edit_time = models.DateTimeField(auto_now=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Change on task {self.task.id} by {self.user} at {self.edit_time}"


def is_diff(obj1, obj2):
    str_rep1: str = str(obj1)
    str_rep2: str = str(obj2)

    return str_rep1 != str_rep2


@receiver(pre_save, sender=Task)
def log_changes(sender, **kwargs):
    new_obj = kwargs["instance"].__dict__
    existing_obj = (
        Task.objects.filter(id=kwargs["instance"].id)[0].__dict__
        if Task.objects.filter(id=kwargs["instance"].id).exists()
        else None
    )
    obj_keys: list = (
        ["status"] if existing_obj is not None else []
    )  # list(existing_obj.keys()) if existing_obj is not None else []
    _ = obj_keys.remove("_state") if "_state" in obj_keys else None
    print(f"\n\n{kwargs}\n\n")
    print(f"\n\n{sender}\n\n")
    print(f"\n\n{new_obj}\n\n")
    print(f"\n\n{existing_obj}\n\n")

    diff: dict = {}

    if existing_obj is not None:
        diff = {
            i: (new_obj[i], existing_obj[i])
            for i in obj_keys
            if is_diff(new_obj[i], existing_obj[i])
        }

        chg = Changelog(
            diff=json.dumps(diff),
            task=kwargs["instance"],
            user=kwargs["instance"].user,
        )
        print(f"\n\n{chg.__dict__}\n\n")
        chg.save()

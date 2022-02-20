# from django.views import View
# from django.http.response import JsonResponse
from tasks.models import Task, Changelog, STATUS_CHOICES
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer, Field
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    CharFilter,
    ChoiceFilter,
    DateTimeFilter,
    NumberFilter,
)


import json


class TaskFilter(FilterSet):
    title = CharFilter(
        lookup_expr="icontains"
    )  # Applying the filter - Title 'contains' search term?
    status = ChoiceFilter(choices=STATUS_CHOICES)


class ChangelogFilter(FilterSet):
    id = NumberFilter(lookup_expr="exact")
    edit_time = DateTimeFilter(lookup_expr="gte")


class ChangesSerializer(Field):
    def to_representation(self, instance):
        return json.loads(instance)

    def to_internal_value(self, data):
        return None


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("username",)


class ChangelogSerializer(ModelSerializer):
    class Meta:
        model = Changelog
        fields = (
            "task",
            "old_status",
            "new_status",
            "edit_time",
            # "user",
        )


class TaskSerializer(ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            "user",
            "id",
            "title",
            "description",
            # "completed",
            "status",
        )


class TaskViewSet(LoginRequiredMixin, ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        object = Task.objects.get(id=self.kwargs["pk"])
        serializer.save()
        new_status = serializer._kwargs["data"]["status"]

        print(object.status, new_status)

        if object.status != new_status:
            Changelog(
                old_status=object.status,  # json.dumps(diff),
                new_status=new_status,
                task=object,
            ).save()


class ChangelogViewSet(ReadOnlyModelViewSet):
    queryset = Changelog.objects.all()
    serializer_class = ChangelogSerializer

    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = ChangelogFilter

    def get_queryset(self, *args, **kwargs):
        print(kwargs)
        if "task_pk" in self.request.parser_context["kwargs"]:
            # print(f"\n\nTotal request=\n\n{str(self.request.user)}\n\n")
            return Changelog.objects.filter(
                task__user=self.request.task.user,
                task=self.request.parser_context["kwargs"]["task_pk"],
            )
        return Changelog.objects.filter(task__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(task__user=self.request.user)

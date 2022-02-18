from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin

from tasks.models import Task, Changelog
from tasks.utils import AuthMixin, ListViewWithSearch
from tasks.forms import UserAuthenticationForm, UserCreationFormCustom, TaskCreateForm


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/tasks")
    else:
        return HttpResponseRedirect("/user/login")


class UserLoginView(LoginView):
    form_class = UserAuthenticationForm
    template_name = "user_login.html"
    success_url = "/user/login/"


class UserCreateView(CreateView):
    form_class = UserCreationFormCustom
    template_name = "user_create.html"
    success_url = "/tasks/"


class GenericTaskUpdateView(AuthMixin, UpdateView):
    form_class = TaskCreateForm
    template_name = "task_update.html"

    def form_valid(self, form):
        if "status" in form.changed_data:
            Changelog(
                old_status=Task.objects.get(id=self.object.id).status,
                new_status=form.cleaned_data["status"],
                task=self.object,
            ).save()

        self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class GenericTaskCreateView(AuthMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class GenericTaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "task_detail.html"

    def get_success_url(self):
        return Task.objects.filter(deleted=False, user=self.request.user).exclude(
            status="COMPLETED"
        )


class GenericTaskDeleteView(AuthMixin, DeleteView):
    template_name = "task_delete.html"


class GenericTaskView(LoginRequiredMixin, ListViewWithSearch):
    queryset = (
        Task.objects.filter(deleted=False).exclude(status="COMPLETED").order_by("id")
    )
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 5


class CompleteTaskView(AuthMixin, View):
    def get(self, request, pk):
        tasks = Task.objects.filter(id=pk, user=self.request.user)
        tasks.update(status="COMPLETED")

        return HttpResponseRedirect("/tasks")


class CompletedTasksView(AuthMixin, ListViewWithSearch):
    queryset = Task.objects.filter(status="COMPLETED").order_by("id")
    template_name = "completed.html"
    context_object_name = "completed"
    paginate_by = 5


class AllTasksView(AuthMixin, ListViewWithSearch):
    queryset = Task.objects.all().order_by("id")
    template_name = "all_tasks.html"
    context_object_name = "all_tasks"
    paginate_by = 5


def session_storage_view(request):
    total_views = (
        int(request.session.get("total_views"))
        if request.session.get("total_views") is not None
        else 0
    )
    request.session["total_views"] = total_views + 1

    return HttpResponse(f"<h1>Total number of views = {total_views}</h1>")

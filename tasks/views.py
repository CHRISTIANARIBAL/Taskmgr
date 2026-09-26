
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Task, TaskUpdate


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

    return render(request, "tasks/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    if request.user.groups.filter(name="Programmer").exists():

        tasks = Task.objects.filter(
            assigned_to=request.user
        ).order_by("-updated_at")

        return render(
            request,
            "tasks/programmer_dashboard.html",
            {
                "tasks": tasks,
                "status_choices": Task.STATUS_CHOICES,
            }
        )

    return render(request, "tasks/no_access.html")


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        assigned_to=request.user
    )

    updates = task.updates.select_related("user").order_by("-created_at")

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "updates": updates,
        }
    )


@login_required
def start_task(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        assigned_to=request.user
    )

    if task.status == "pending":
        task.status = "in_progress"
        task.save()

    return redirect("task_detail", task_id=task.id)


@login_required
def mark_updated(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        assigned_to=request.user
    )

    if task.status == "in_progress":
        task.status = "updated"
        task.save()

    return redirect("task_detail", task_id=task.id)


@login_required
def add_task_update(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        assigned_to=request.user
    )

    if request.method == "POST":
        message = request.POST.get("message", "").strip()

        if message:
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                message=message
            )

            task.save()

    return redirect("task_detail", task_id=task.id)


@login_required
def change_task_status(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        assigned_to=request.user
    )

    if request.method == "POST":
        status = request.POST.get("status")

        allowed_statuses = ["pending", "in_progress", "updated"]

        if status in allowed_statuses:
            task.status = status
            task.save()

    return redirect("dashboard")


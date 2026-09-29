
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth.models import User
from django.http import JsonResponse


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
    if not (
        request.user.is_superuser
        or request.user.groups.filter(name="Programmer").exists()
    ):
        return render(request, "tasks/no_access.html")

    programmers = User.objects.filter(
        groups__name="Programmer",
        is_superuser=False
    ).order_by("username").distinct()

    tasks = Task.objects.all().order_by("-updated_at")
    unassigned_tasks = tasks.filter(assigned_to__isnull=True)

    programmer_tasks = []

    for programmer in programmers:
        programmer_tasks.append({
            "programmer": programmer,
            "tasks": tasks.filter(assigned_to=programmer)
        })

    return render(
        request,
        "tasks/programmer_dashboard.html",
        {
            "tasks": tasks,
            "unassigned_tasks": unassigned_tasks,
            "programmers": programmers,
            "programmer_tasks": programmer_tasks,
            "status_choices": Task.STATUS_CHOICES,
        }
    )

@login_required
def add_task(request):
    if not request.user.is_superuser:
        return redirect("dashboard")

    if request.method == "POST":
        print("POST DATA:", request.POST)
        print("FILES DATA:", request.FILES)
        print("FILES LIST:", request.FILES.getlist("images"))

        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if title:
            task = Task.objects.create(
                title=title,
                description=description
            )

            for image in request.FILES.getlist("images"):
                print("SAVING IMAGE:", image.name)
                TaskImage.objects.create(
                    task=task,
                    image=image
                )

            return redirect("dashboard")

    return render(request, "tasks/add_task.html")


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    updates = task.updates.select_related("user").order_by("-created_at")

    checklist_items = task.checklist_items.filter(
        user=request.user
    ).order_by("created_at")

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "updates": updates,
            "checklist_items": checklist_items,
        }
    )

@login_required
def start_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.status == "pending":
        task.status = "in_progress"
        task.save()

    return redirect("task_detail", task_id=task.id)


@login_required
def mark_updated(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.status == "in_progress":
        task.status = "updated"
        task.save()

    return redirect("task_detail", task_id=task.id)



@login_required
def change_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        status = request.POST.get("status")

        allowed_statuses = ["pending", "in_progress", "updated"]

        if status in allowed_statuses:
            task.status = status
            task.save()

    return redirect("dashboard")

@login_required
def assign_task(request, task_id):
    if not request.user.is_superuser:
        return redirect("dashboard")

    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        programmer_id = request.POST.get("programmer")

        if programmer_id:
            programmer = get_object_or_404(
                User,
                id=programmer_id,
                groups__name="Programmer",
                is_superuser=False
            )

            task.assigned_to = programmer
            task.save()

    return redirect("dashboard")

@login_required
def edit_task(request, task_id):
    if not request.user.is_superuser:
        return redirect("dashboard")

    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if title:
            task.title = title
            task.description = description
            task.save()

            for image in request.FILES.getlist("images"):
                TaskImage.objects.create(
                    task=task,
                    image=image
                )

            return redirect("dashboard")

    return render(request, "tasks/edit_task.html", {"task": task})

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
def delete_task_image(request, image_id):
    if not request.user.is_superuser:
        return redirect("dashboard")

    image = get_object_or_404(TaskImage, id=image_id)
    task_id = image.task.id

    if request.method == "POST":
        image.image.delete(save=False)
        image.delete()

    return redirect("edit_task", task_id=task_id)

@login_required
def change_task_progress(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        try:
            progress = int(request.POST.get("progress", 0))
        except (TypeError, ValueError):
            progress = 0

        progress = max(0, min(100, progress))

        task.progress = progress
        task.save()

        return JsonResponse({
            "success": True,
            "progress": progress
        })

    return JsonResponse({
        "success": False
    }, status=400)

@login_required
def delete_task(request, task_id):
    if not request.user.is_superuser:
        return redirect("dashboard")

    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        task.delete()

    return redirect("dashboard")

@login_required
def add_checklist_item(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        assigned_to=request.user
    )

    if request.method == "POST":
        item = request.POST.get("item", "").strip()

        if item:
            TaskChecklist.objects.create(
                task=task,
                user=request.user,
                item=item
            )

    return redirect("task_detail", task_id=task.id)


@login_required
def toggle_checklist_item(request, item_id):
    checklist = get_object_or_404(
        TaskChecklist,
        id=item_id,
        user=request.user
    )

    if request.method == "POST":
        checklist.is_completed = not checklist.is_completed
        checklist.save()

    return redirect("task_detail", task_id=checklist.task.id)


@login_required
def delete_checklist_item(request, item_id):
    checklist = get_object_or_404(
        TaskChecklist,
        id=item_id,
        user=request.user
    )

    task_id = checklist.task.id

    if request.method == "POST":
        checklist.delete()

    return redirect("task_detail", task_id=task_id)

@login_required
def edit_checklist_item(request, item_id):
    checklist = get_object_or_404(
        TaskChecklist,
        id=item_id,
        user=request.user
    )

    if request.method == "POST":
        item = request.POST.get("item", "").strip()

        if item:
            checklist.item = item
            checklist.save()

    return redirect("task_detail", task_id=checklist.task.id)
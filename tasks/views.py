
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone

def can_manage_task(task, user):
    return (
        user.is_superuser
        or task.assigned_to.filter(id=user.id).exists()
    )

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

    tasks = Task.objects.filter(is_completed=False).order_by("-updated_at")
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
    if not request.user.is_superuser and not request.user.groups.filter(name="Programmer").exists():
        return redirect("dashboard")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")

        task = Task.objects.create(
            title=title,
            description=description,
            created_by=request.user
        )

        if request.user.is_superuser:
            programmer_ids = [
                user_id for user_id in request.POST.getlist("assigned_to")
                if user_id
            ]

            if programmer_ids:
                programmers = User.objects.filter(
                    id__in=programmer_ids,
                    groups__name="Programmer",
                    is_superuser=False
                ).distinct()

                task.assigned_to.set(programmers)
        else:
            task.assigned_to.add(request.user)

        for image in request.FILES.getlist("images"):
            TaskImage.objects.create(
                task=task,
                image=image
            )

        return redirect("task_detail", task_id=task.id)

    programmers = User.objects.filter(
        groups__name="Programmer"
    ).order_by("username").distinct()

    return render(
        request,
        "tasks/add_task.html",
        {"programmers": programmers}
    )


@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    can_manage_task = (
        request.user.is_superuser
        or task.assigned_to.filter(id=request.user.id).exists()
    )

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
            "can_manage_task": can_manage_task,
        }
    )

@login_required
def start_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not can_manage_task(task, request.user):
        return redirect("task_detail", task_id=task.id)

    if task.status == "pending":
        task.status = "in_progress"
        task.save()

    return redirect("task_detail", task_id=task.id)


@login_required
def mark_updated(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not can_manage_task(task, request.user):
        return redirect("task_detail", task_id=task.id)

    if task.status == "in_progress":
        task.status = "updated"
        task.save()

    return redirect("task_detail", task_id=task.id)



@login_required
def change_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not can_manage_task(task, request.user):
        return redirect("task_detail", task_id=task.id)

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
        programmer_ids = [
            user_id for user_id in request.POST.getlist("programmer")
            if user_id
        ]

        programmers = User.objects.filter(
            id__in=programmer_ids,
            groups__name="Programmer",
            is_superuser=False
        ).distinct()

        task.assigned_to.set(programmers)

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
    task = get_object_or_404(Task, id=task_id)

    if not can_manage_task(task, request.user):
        return redirect("task_detail", task_id=task.id)

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
    if not can_manage_task(task, request.user):
        return JsonResponse({
            "success": False,
            "error": "You do not have permission to modify this task."
        }, status=403)

    if request.method == "POST":
        try:
            progress = int(request.POST.get("progress", 0))
        except (TypeError, ValueError):
            progress = 0

        progress = max(0, min(100, progress))

        task.progress = progress

        # If a completed task is moved below 100%,
        # return it to the active task list.
        if task.is_completed and progress < 100:
            task.is_completed = False
            task.completed_at = None
            task.completed_by = None

        task.save()

        return JsonResponse({
            "success": True,
            "progress": progress,
            "is_completed": task.is_completed
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
    task = get_object_or_404(Task, id=task_id)

    if not can_manage_task(task, request.user):
        return redirect("task_detail", task_id=task.id)

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

@login_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not request.user.is_superuser and not task.assigned_to.filter(id=request.user.id).exists():
        return redirect("task_detail", task_id=task.id)

    if request.method == "POST":
        if task.progress == 100:
            task.is_completed = True
            task.completed_at = timezone.now()
            task.completed_by = request.user
            task.save()

    return redirect("task_detail", task_id=task.id)

@login_required
def completed_tasks(request):
    tasks = Task.objects.filter(
        is_completed=True
    ).prefetch_related(
        "assigned_to"
    ).select_related(
        "completed_by"
    ).order_by("-completed_at")

    return render(
        request,
        "tasks/completed_tasks.html",
        {
            "tasks": tasks,
        }
    )

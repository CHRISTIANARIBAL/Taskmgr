from django.contrib import admin
from .models import Task, TaskUpdate


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "assigned_users",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "assigned_to",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "assigned_to__username",
    )

    ordering = ("-updated_at",)

    @admin.display(description="Assigned To")
    def assigned_users(self, obj):
        return ", ".join(
            user.username for user in obj.assigned_to.all()
        )


@admin.register(TaskUpdate)
class TaskUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "task",
        "user",
        "message",
        "created_at",
    )

    list_filter = (
        "user",
        "created_at",
    )

    search_fields = (
        "task__title",
        "message",
        "user__username",
    )

    ordering = ("-created_at",)
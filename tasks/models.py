from django.db import models
from django.contrib.auth.models import User


class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("updated", "Updated"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TaskUpdate(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="updates"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.title} - {self.user}"
    

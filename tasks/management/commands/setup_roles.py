from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Create task management groups"

    def handle(self, *args, **kwargs):
        Group.objects.get_or_create(name="Admin")
        Group.objects.get_or_create(name="Programmer")

        self.stdout.write(
            self.style.SUCCESS("Admin and Programmer groups created.")
        )
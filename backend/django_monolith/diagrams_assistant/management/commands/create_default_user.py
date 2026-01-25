from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a default user for development."

    def handle(self, *args, **options):
        username = "testuser"
        password = "testpassword"
        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating user: {username}")
            User.objects.create_user(username=username, password=password)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created user: {username}")
            )
        else:
            self.stdout.write(self.style.WARNING(f"User {username} already exists."))

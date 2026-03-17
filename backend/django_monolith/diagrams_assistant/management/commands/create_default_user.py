from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from user_auth.models import EmailVerificationToken, UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a default verified user for development."

    def handle(self, *args, **options):
        username = "testuser"
        password = "testpassword"
        email = "testuser@example.com"

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating user: {username}")
            user = User.objects.create_user(
                username=username, password=password, email=email
            )
            UserProfile.objects.create(
                user=user, terms_accepted=True, terms_accepted_at=timezone.now()
            )
            EmailVerificationToken.objects.create(user=user, verified_at=timezone.now())
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created verified user: {username}")
            )
        else:
            self.stdout.write(self.style.WARNING(f"User {username} already exists."))

"""Factory Boy factories for test data generation."""

import factory
from django.contrib.auth import get_user_model
from diagrams_assistant.models import Diagram, DiagramVersion, ChatMessage
from quota_management.models import UserQuota, DiagramGenerationLog
from user_auth.models import SocialAccount

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = "User"
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set a default password for created users."""
        if create:
            password = extracted if extracted else "testpass123"
            obj.set_password(password)
            obj.save()


class DiagramFactory(factory.django.DjangoModelFactory):
    """Factory for creating test diagrams."""

    class Meta:
        model = Diagram

    title = factory.Sequence(lambda n: f"Diagram {n}")
    owner = factory.SubFactory(UserFactory)
    agent_history = "[]"


class DiagramVersionFactory(factory.django.DjangoModelFactory):
    """Factory for creating test diagram versions."""

    class Meta:
        model = DiagramVersion

    diagram = factory.SubFactory(DiagramFactory)
    image_uri = "gs://test-bucket/test-image.png"
    prompt_text = factory.Sequence(lambda n: f"Test prompt {n}")


class ChatMessageFactory(factory.django.DjangoModelFactory):
    """Factory for creating test chat messages."""

    class Meta:
        model = ChatMessage

    diagram = factory.SubFactory(DiagramFactory)
    role = "user"
    content = factory.Sequence(lambda n: f"Test message {n}")


class UserQuotaFactory(factory.django.DjangoModelFactory):
    """Factory for creating test user quotas."""

    class Meta:
        model = UserQuota

    user = factory.SubFactory(UserFactory)
    quota_limit = 10
    period = "day"
    is_unlimited = False


class DiagramGenerationLogFactory(factory.django.DjangoModelFactory):
    """Factory for creating test diagram generation logs."""

    class Meta:
        model = DiagramGenerationLog

    user = factory.SubFactory(UserFactory)


class SocialAccountFactory(factory.django.DjangoModelFactory):
    """Factory for creating test social accounts."""

    class Meta:
        model = SocialAccount

    user = factory.SubFactory(UserFactory)
    provider = "google"
    uid = factory.Sequence(lambda n: f"google_uid_{n}")
    extra_data = factory.Dict(
        {
            "email": factory.LazyAttribute(lambda obj: obj.factory_parent.user.email),
            "given_name": "Test",
            "family_name": "User",
        }
    )

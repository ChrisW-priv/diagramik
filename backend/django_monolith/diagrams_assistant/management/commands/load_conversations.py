import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from diagrams_assistant.models import ChatMessage, Diagram, DiagramVersion

User = get_user_model()

REPO_ROOT = (
    Path(__file__).resolve().parents[5]
)  # backend/django_monolith/diagrams_assistant/management/commands -> repo root
DEFAULT_CONVERSATIONS_DIR = REPO_ROOT / "conversations"


class Command(BaseCommand):
    help = "Load conversation JSON files into Diagram, DiagramVersion, and ChatMessage records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            type=str,
            default=str(DEFAULT_CONVERSATIONS_DIR),
            help="Directory containing conversation JSON files (default: <repo>/conversations/)",
        )

    def handle(self, *args, **options):
        conversations_dir = Path(options["dir"])
        if not conversations_dir.is_dir():
            self.stderr.write(
                self.style.ERROR(f"Directory not found: {conversations_dir}")
            )
            return

        owner = self._ensure_user()
        json_files = sorted(conversations_dir.glob("*.json"))

        if not json_files:
            self.stderr.write(
                self.style.WARNING(f"No JSON files found in {conversations_dir}")
            )
            return

        for json_file in json_files:
            self._load_conversation(json_file, owner)

    def _ensure_user(self):
        username = "testuser"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "password": "!"
            },  # unusable password; create_default_user sets real one
        )
        if created:
            user.set_password("testpassword")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))
        return user

    @transaction.atomic
    def _load_conversation(self, json_file, owner):
        file_stem = json_file.stem  # e.g. "convo1"
        prefix = f"[{file_stem}]"

        # Idempotency: delete existing diagrams with this prefix
        deleted_count, _ = Diagram.objects.filter(
            title__startswith=prefix, owner=owner
        ).delete()
        if deleted_count:
            self.stdout.write(
                f"  Deleted {deleted_count} existing record(s) for {prefix}"
            )

        data = json.loads(json_file.read_text())
        messages = data.get("messages", [])

        # Extract successful tool results and pair with user prompts
        versions_data = []
        chat_messages_data = []
        last_user_text = ""
        first_title = None

        for msg in messages:
            role = msg.get("role")

            # Track the last user text prompt
            if role == "user" and msg.get("content"):
                for content_item in msg["content"]:
                    if content_item.get("type") == "text":
                        last_user_text = content_item["text"]
                        break

            # Check for successful tool results
            if role == "user" and msg.get("tool_results"):
                for _call_id, result in msg["tool_results"].items():
                    if result.get("isError"):
                        continue

                    result_text = ""
                    for content_item in result.get("content", []):
                        if content_item.get("type") == "text":
                            result_text = content_item["text"]
                            break

                    try:
                        parsed = json.loads(result_text)
                    except (json.JSONDecodeError, TypeError):
                        continue

                    uri = parsed.get("uri", "")
                    title = parsed.get("title", "")

                    if not uri:
                        continue

                    if first_title is None:
                        first_title = title

                    versions_data.append(
                        {
                            "image_uri": uri,
                            "prompt_text": last_user_text,
                        }
                    )

                    # Chat message pairs: user prompt + assistant response
                    if last_user_text:
                        chat_messages_data.append(
                            {"role": "user", "content": last_user_text}
                        )
                    chat_messages_data.append(
                        {"role": "assistant", "content": "Image Ready!"}
                    )

        if not versions_data:
            self.stdout.write(
                self.style.WARNING(
                    f"  No successful diagrams found in {json_file.name}"
                )
            )
            return

        diagram_title = f"{prefix} {first_title or 'Untitled'}"
        diagram = Diagram.objects.create(
            owner=owner,
            title=diagram_title,
            agent_history=json.dumps(messages),
        )

        diagram_versions = [
            DiagramVersion(diagram=diagram, **vd) for vd in versions_data
        ]
        DiagramVersion.objects.bulk_create(diagram_versions)

        chat_msgs = [ChatMessage(diagram=diagram, **cmd) for cmd in chat_messages_data]
        ChatMessage.objects.bulk_create(chat_msgs)

        self.stdout.write(
            self.style.SUCCESS(
                f"  Loaded {json_file.name}: "
                f"{len(versions_data)} version(s), "
                f"{len(chat_messages_data)} message(s) "
                f'-> "{diagram_title}"'
            )
        )

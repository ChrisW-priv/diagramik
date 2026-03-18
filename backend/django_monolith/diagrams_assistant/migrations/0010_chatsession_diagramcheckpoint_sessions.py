"""Add ChatSession, DiagramCheckpoint models and session fields."""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "diagrams_assistant",
            "0009_remove_diagramgenerationlog_diagrams_as_user_id_031df4_idx_and_more",
        ),
    ]

    operations = [
        # 1. Create ChatSession model
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("agent_history", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "diagram",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_sessions",
                        to="diagrams_assistant.diagram",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        # 2. Add session FK to DiagramVersion
        migrations.AddField(
            model_name="diagramversion",
            name="session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="versions",
                to="diagrams_assistant.chatsession",
            ),
        ),
        # 3. Add agent_history_snapshot, source_code, diagram_type to DiagramVersion
        migrations.AddField(
            model_name="diagramversion",
            name="agent_history_snapshot",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="diagramversion",
            name="source_code",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="diagramversion",
            name="diagram_type",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        # 4. Add session FK to ChatMessage
        migrations.AddField(
            model_name="chatmessage",
            name="session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="diagrams_assistant.chatsession",
            ),
        ),
        # 5. Create DiagramCheckpoint model
        migrations.CreateModel(
            name="DiagramCheckpoint",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, default="")),
                ("source_code", models.TextField()),
                (
                    "diagram_type",
                    models.CharField(
                        choices=[
                            ("technical", "Technical"),
                            ("mermaid", "Mermaid"),
                        ],
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "diagram",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkpoints",
                        to="diagrams_assistant.diagram",
                    ),
                ),
                (
                    "version",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkpoint",
                        to="diagrams_assistant.diagramversion",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("diagram", "name"),
                        name="unique_checkpoint_name_per_diagram",
                    )
                ],
            },
        ),
        # 6. Add parent_checkpoint FK to ChatSession
        migrations.AddField(
            model_name="chatsession",
            name="parent_checkpoint",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="diagrams_assistant.diagramcheckpoint",
            ),
        ),
        # 7. Add active_session FK to Diagram
        migrations.AddField(
            model_name="diagram",
            name="active_session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="diagrams_assistant.chatsession",
            ),
        ),
    ]

"""Migrate existing data to use ChatSession model.

For each existing Diagram:
1. Create a default ChatSession with the diagram's agent_history
2. Link existing ChatMessages and DiagramVersions to the session
3. Set diagram.active_session to the new session
"""

from django.db import migrations


def migrate_to_sessions(apps, schema_editor):
    Diagram = apps.get_model("diagrams_assistant", "Diagram")
    ChatSession = apps.get_model("diagrams_assistant", "ChatSession")
    ChatMessage = apps.get_model("diagrams_assistant", "ChatMessage")
    DiagramVersion = apps.get_model("diagrams_assistant", "DiagramVersion")

    for diagram in Diagram.objects.all():
        session = ChatSession.objects.create(
            diagram=diagram,
            agent_history=diagram.agent_history or "",
        )
        ChatMessage.objects.filter(diagram=diagram).update(session=session)
        DiagramVersion.objects.filter(diagram=diagram).update(session=session)
        diagram.active_session = session
        diagram.save(update_fields=["active_session"])


def reverse_migration(apps, schema_editor):
    Diagram = apps.get_model("diagrams_assistant", "Diagram")

    for diagram in Diagram.objects.all():
        if diagram.active_session_id:
            ChatSession = apps.get_model("diagrams_assistant", "ChatSession")
            try:
                session = ChatSession.objects.get(pk=diagram.active_session_id)
                diagram.agent_history = session.agent_history
                diagram.save(update_fields=["agent_history"])
            except ChatSession.DoesNotExist:
                pass


class Migration(migrations.Migration):
    dependencies = [
        ("diagrams_assistant", "0010_chatsession_diagramcheckpoint_sessions"),
    ]

    operations = [
        migrations.RunPython(migrate_to_sessions, reverse_migration),
    ]

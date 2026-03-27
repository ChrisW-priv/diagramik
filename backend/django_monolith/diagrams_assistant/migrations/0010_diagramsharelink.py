import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("diagrams_assistant", "0009_remove_diagramgenerationlog_diagrams_as_user_id_031df4_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiagramShareLink",
            fields=[
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("diagram_version", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="share_links", to="diagrams_assistant.diagramversion")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

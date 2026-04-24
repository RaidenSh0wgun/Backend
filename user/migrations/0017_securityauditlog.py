from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0016_remove_ids"),
    ]

    operations = [
        migrations.CreateModel(
            name="SecurityAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("role_change", "Role Change"), ("role_switch_attempt", "Role Switch Attempt"), ("media_upload", "Media Upload"), ("email_verification_request", "Email Verification Request")], max_length=50)),
                ("detail", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="security_logs", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

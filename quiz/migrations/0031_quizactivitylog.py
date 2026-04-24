from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0030_merge_20260413_1028"),
        ("user", "0017_securityauditlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuizActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("answer_change", "Answer Change"), ("page_refresh", "Page Refresh"), ("focus_loss", "Focus Loss"), ("copy_paste", "Copy Paste"), ("screenshot", "Screenshot"), ("tab_switch", "Tab Switch"), ("submit", "Submit")], max_length=50)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_logs", to="quiz.quiz")),
                ("student", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="quiz_activity_logs", to="user.studentprofile")),
            ],
        ),
    ]

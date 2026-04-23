from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("course", "0006_course_passkey_enrollment_used_passkey_and_more"),
    ]
    operations = [
        migrations.AddField(
            model_name="course",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]

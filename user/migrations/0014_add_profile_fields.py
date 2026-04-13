from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0013_alter_instructorprofile_id_alter_studentprofile_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="sex",
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="avatar_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="studentprofile",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="instructorprofile",
            name="bio",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="instructorprofile",
            name="sex",
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="instructorprofile",
            name="avatar_url",
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="instructorprofile",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
    ]

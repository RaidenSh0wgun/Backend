from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('user', '0018_alter_instructorprofile_avatar_url_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reporter_username', models.CharField(blank=True, max_length=150)),
                ('reporter_email', models.EmailField(blank=True, max_length=254)),
                ('reporter_role', models.CharField(blank=True, max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('bug', 'Bug'), ('problem', 'Problem'), ('feature', 'Feature Request'), ('other', 'Other')], max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reporter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

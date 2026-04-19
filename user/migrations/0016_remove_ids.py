# Generated migration to remove student_id and instructor_id fields

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0015_alter_instructorprofile_avatar_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='student_id',
        ),
        migrations.RemoveField(
            model_name='instructorprofile',
            name='instructor_id',
        ),
    ]

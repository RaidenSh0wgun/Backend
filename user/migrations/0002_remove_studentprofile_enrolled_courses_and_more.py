from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]
    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='enrolled_courses',
        ),
        migrations.RemoveField(
            model_name='studentprofile',
            name='user',
        ),
        migrations.DeleteModel(
            name='InstructorProfile',
        ),
        migrations.DeleteModel(
            name='StudentProfile',
        ),
    ]

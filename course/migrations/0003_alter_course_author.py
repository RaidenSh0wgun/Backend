import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0002_course_author_alter_course_title'),
        ('user', '0006_instructorprofile_full_name_studentprofile_full_name_and_more'),
    ]
    operations = [
        migrations.AlterField(
            model_name='course',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_courses', to='user.instructorprofile', verbose_name='Created by'),
        ),
    ]

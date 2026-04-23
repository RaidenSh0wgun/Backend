import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0001_initial'),
        ('user', '0006_instructorprofile_full_name_studentprofile_full_name_and_more'),
    ]
    operations = [
        migrations.AddField(
            model_name='course',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='courses_created', to='user.instructorprofile', verbose_name='Instructor'),
        ),
        migrations.AlterField(
            model_name='course',
            name='title',
            field=models.CharField(max_length=100),
        ),
    ]

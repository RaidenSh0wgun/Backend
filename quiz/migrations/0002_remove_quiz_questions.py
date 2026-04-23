from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0001_initial'),
    ]
    operations = [
        migrations.RemoveField(
            model_name='quiz',
            name='questions',
        ),
    ]

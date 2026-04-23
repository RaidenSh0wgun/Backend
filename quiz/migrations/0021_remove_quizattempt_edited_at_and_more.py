from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0020_merge_20260313_1555'),
    ]
    operations = [
        migrations.RemoveField(
            model_name='quizattempt',
            name='edited_at',
        ),
        migrations.RemoveField(
            model_name='quizattempt',
            name='edited_by',
        ),
    ]

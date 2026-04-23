from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0021_remove_quizattempt_edited_at_and_more'),
    ]
    operations = [
        migrations.AlterModelOptions(
            name='quiz',
            options={'verbose_name_plural': 'Quizzes'},
        ),
    ]

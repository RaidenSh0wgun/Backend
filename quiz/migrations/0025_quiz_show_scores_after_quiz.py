from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0024_alter_quiz_options'),
    ]
    operations = [
        migrations.AddField(
            model_name='quiz',
            name='show_scores_after_quiz',
            field=models.BooleanField(default=True, help_text='Whether students can view their scores after completing the quiz'),
        ),
    ]

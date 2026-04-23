import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0007_delete_questionchoice_remove_question_question_type_and_more'),
    ]
    operations = [
        migrations.RemoveField(
            model_name='question',
            name='calories_burned',
        ),
        migrations.AddField(
            model_name='question',
            name='Quiz',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quiz.quiz'),
        ),
    ]

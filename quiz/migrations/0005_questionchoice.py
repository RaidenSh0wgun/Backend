import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_question_delete_question_types'),
    ]
    operations = [
        migrations.CreateModel(
            name='questionChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice_text', models.CharField(max_length=255)),
                ('is_correct', models.BooleanField(default=False)),
                ('question_type', models.CharField(choices=[('MCQ', 'Multiple Choice Question'), ('TF', 'True/False'), ('SA', 'Short Answer')], default='MCQ', max_length=3)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='quiz.question')),
            ],
        ),
    ]

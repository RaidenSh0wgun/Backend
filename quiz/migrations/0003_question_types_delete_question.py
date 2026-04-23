import django.core.validators

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_remove_quiz_questions'),
    ]
    operations = [
        migrations.CreateModel(
            name='Question_Types',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('points', models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('qtype', models.CharField(choices=[('mcq', 'Multiple Choice'), ('tf', 'True/False'), ('ident', 'Identification'), ('essay', 'Essay')], default='mcq', max_length=10)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='quiz.quiz')),
            ],
        ),
        migrations.DeleteModel(
            name='Question',
        ),
    ]

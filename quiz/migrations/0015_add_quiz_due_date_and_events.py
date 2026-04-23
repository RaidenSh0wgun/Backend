from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0004_alter_course_created_at_alter_course_updated_at'),
        ('quiz', '0014_quizattempt'),
    ]
    operations = [
        migrations.AddField(
            model_name='quiz',
            name='due_date',
            field=models.DateTimeField(blank=True, help_text='Quiz deadline for calendar', null=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='question',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='title',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='quizattempt',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterUniqueTogether(
            name='quiz',
            unique_together={('course', 'title')},
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0009_rename_quiz_question_quiz_and_more'),
        ('user', '0002_remove_studentprofile_enrolled_courses_and_more'),
    ]
    operations = [
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='Course',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
        migrations.DeleteModel(
            name='Quiz',
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quiz", "0021_remove_quizattempt_edited_at_and_more"),
    ]
    operations = [
        migrations.AlterField(
            model_name="question",
            name="question_type",
            field=models.CharField(
                choices=[
                    ("identification", "Identification"),
                    ("enumeration", "Enumeration"),
                    ("mcq", "Multiple choice"),
                    ("tf", "True or false"),
                ],
                default="mcq",
                max_length=20,
            ),
        ),
    ]

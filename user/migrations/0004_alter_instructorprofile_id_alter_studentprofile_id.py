from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_initial'),
    ]
    operations = [
        migrations.AlterField(
            model_name='instructorprofile',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]

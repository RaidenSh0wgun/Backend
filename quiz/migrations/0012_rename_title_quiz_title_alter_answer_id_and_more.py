from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0011_initial'),
    ]
    operations = [
        migrations.RenameField(
            model_name='quiz',
            old_name='Title',
            new_name='title',
        ),
        migrations.AlterField(
            model_name='answer',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='course',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='question',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='author',
            field=models.CharField(blank=True, max_length=50, verbose_name='Author'),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]

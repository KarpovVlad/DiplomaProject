# Generated by Django 5.0.4 on 2024-05-13 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_course_semester'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseapplication',
            name='semester',
            field=models.IntegerField(choices=[(3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8')], default=3),
        ),
    ]

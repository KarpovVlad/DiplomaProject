# Generated by Django 5.0.4 on 2024-05-13 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_alter_courseapplication_semester'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='catalog',
            field=models.IntegerField(choices=[(1, 'Catalog 1'), (2, 'Catalog 2'), (3, 'Catalog 3'), (4, 'Catalog 4'), (5, 'Catalog 5'), (6, 'Catalog 6')], default=1),
        ),
        migrations.AlterField(
            model_name='course',
            name='semester',
            field=models.IntegerField(choices=[(3, '3rd Semester'), (4, '4th Semester'), (5, '5th Semester'), (6, '6th Semester'), (7, '7th Semester'), (8, '8th Semester')], default=3),
        ),
    ]

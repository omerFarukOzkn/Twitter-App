# Generated by Django 5.0 on 2024-03-09 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_profile_follow_alter_profile_follower'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='follower',
            field=models.ManyToManyField(blank=True, related_name='takipci', to='user.profile', verbose_name='Takipçiler'),
        ),
    ]

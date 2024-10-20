# Generated by Django 4.2.11 on 2024-04-12 18:01

from django.db import migrations

FLAG_NAME = "wacz-playback"

def create_wacz_playback_feature_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    flag = Flag(
        name=FLAG_NAME,
        testing=True
    )
    flag.save()

def delete_wacz_playback_feature_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    flags = Flag.objects.filter(name=FLAG_NAME)
    flags.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0038_auto_20240318_2102'),
        ('waffle', '0004_update_everyone_nullbooleanfield'),
    ]

    operations = [
        migrations.RunPython(create_wacz_playback_feature_flag, delete_wacz_playback_feature_flag),
    ]

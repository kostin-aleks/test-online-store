# Generated by Django 5.1.1 on 2024-09-06 10:36

from django.db import migrations
from django.db import connection


def check_and_update(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("""
        SET @content_id = (SELECT id
        FROM django_content_type WHERE app_label='auth' AND model='user')
        """)

        cursor.execute("""
        INSERT INTO auth_permission
        (content_type_id, codename, name)
        VALUES
        (@content_id, 'manager', 'Store manager')
        """)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(check_and_update),
    ]

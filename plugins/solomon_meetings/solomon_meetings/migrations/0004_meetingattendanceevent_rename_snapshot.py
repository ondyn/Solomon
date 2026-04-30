# Generated migration to rename snapshot field to owner_snapshot

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('solomon_meetings', '0003_voteweightstyle_exact_fraction'),
    ]

    operations = [
        migrations.RenameField(
            model_name='meetingattendanceevent',
            old_name='snapshot',
            new_name='owner_snapshot',
        ),
    ]

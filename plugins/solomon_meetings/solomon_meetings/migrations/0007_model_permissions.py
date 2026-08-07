from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("solomon_meetings", "0006_alter_meetingattendanceevent_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="agendaitem",
            options={
                "ordering": ["meeting", "order", "title"],
                "permissions": (
                    ("run_voting_session", "Can create and update voting sessions"),
                ),
                "verbose_name": "Agenda item",
                "verbose_name_plural": "Agenda items",
            },
        ),
        migrations.AlterModelOptions(
            name="meeting",
            options={
                "ordering": ["-date_time", "title"],
                "permissions": (
                    ("manage_meeting_workflow", "Can manage meeting workflow actions"),
                    ("manage_attendance_live", "Can toggle live meeting attendance"),
                    (
                        "sync_ballot_styles",
                        "Can synchronize ballot styles from ownership",
                    ),
                    ("export_meeting_data", "Can export meeting reports"),
                ),
                "verbose_name": "Meeting",
                "verbose_name_plural": "Meetings",
            },
        ),
    ]

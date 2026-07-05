from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("solomon_property", "0003_buildingobject_and_building_parent"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="building",
            options={
                "ordering": ["name"],
                "permissions": (
                    ("import_cuzk_data", "Can import building and flat data from CUZK"),
                    ("calculate_flat_area", "Can calculate and apply flat areas from CUZK shares"),
                ),
                "verbose_name": "Building",
                "verbose_name_plural": "Buildings",
            },
        ),
        migrations.AlterModelOptions(
            name="person",
            options={
                "ordering": ["last_name", "first_name"],
                "permissions": (
                    ("import_contacts_data", "Can import contacts from CSV"),
                    ("export_contacts_data", "Can export contacts to CSV"),
                ),
                "verbose_name": "Person",
                "verbose_name_plural": "Persons",
            },
        ),
        migrations.AlterModelOptions(
            name="propertyowner",
            options={
                "ordering": ["display_name"],
                "permissions": (
                    ("import_owner_data", "Can import owners from text data"),
                ),
                "verbose_name": "Property Owner",
                "verbose_name_plural": "Property Owners",
            },
        ),
    ]

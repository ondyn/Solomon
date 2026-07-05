from django.db import migrations


def copy_permission_assignments(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("users", "Group")
    User = apps.get_model("users", "User")

    permission_pairs = [
        ("solomon_property", "building", "import_cuzk_data", "import_cuzk_data_building"),
        ("solomon_property", "building", "calculate_flat_area", "calculate_flat_area_building"),
        ("solomon_property", "person", "import_contacts_data", "import_contacts_data_person"),
        ("solomon_property", "person", "export_contacts_data", "export_contacts_data_person"),
        ("solomon_property", "propertyowner", "import_owner_data", "import_owner_data_propertyowner"),
    ]

    for app_label, model, old_codename, new_codename in permission_pairs:
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            continue

        old_permission = Permission.objects.filter(content_type=content_type, codename=old_codename).first()
        new_permission = Permission.objects.filter(content_type=content_type, codename=new_codename).first()
        if not old_permission or not new_permission:
            continue

        for group in Group.objects.filter(permissions=old_permission):
            group.permissions.add(new_permission)

        for user in User.objects.filter(user_permissions=old_permission):
            user.user_permissions.add(new_permission)


class Migration(migrations.Migration):

    dependencies = [
        ("solomon_property", "0004_model_permissions"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="building",
            options={
                "ordering": ["name"],
                "permissions": (
                    ("import_cuzk_data_building", "Can import building and flat data from CUZK"),
                    ("calculate_flat_area_building", "Can calculate and apply flat areas from CUZK shares"),
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
                    ("import_contacts_data_person", "Can import contacts from CSV"),
                    ("export_contacts_data_person", "Can export contacts to CSV"),
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
                    ("import_owner_data_propertyowner", "Can import owners from text data"),
                ),
                "verbose_name": "Property Owner",
                "verbose_name_plural": "Property Owners",
            },
        ),
        migrations.RunPython(copy_permission_assignments, migrations.RunPython.noop),
    ]
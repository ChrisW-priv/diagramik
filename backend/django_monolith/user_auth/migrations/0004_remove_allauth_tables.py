# Migration to drop orphaned django-allauth tables from production database.
# These tables were left behind when django-allauth was removed from the codebase.

from django.db import migrations


def drop_allauth_tables(apps, schema_editor):
    """
    Drops all django-allauth tables from the database.

    Tables dropped (in dependency-safe order):
    - socialaccount_socialtoken (OAuth tokens)
    - socialaccount_socialapp_sites (app-site relationships)
    - socialaccount_socialapp (OAuth app configurations)
    - socialaccount_socialaccount (main OAuth accounts - data already migrated)
    - account_emailconfirmation (email confirmations)
    - account_emailaddress (email addresses)

    Using CASCADE to handle any remaining foreign key dependencies.
    """
    tables_to_drop = [
        "socialaccount_socialtoken",
        "socialaccount_socialapp_sites",
        "socialaccount_socialapp",
        "socialaccount_socialaccount",
        "account_emailconfirmation",
        "account_emailaddress",
    ]

    with schema_editor.connection.cursor() as cursor:
        print("Dropping django-allauth tables...")

        for table_name in tables_to_drop:
            # Check if table exists before dropping
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """,
                [table_name],
            )
            table_exists = cursor.fetchone()[0]

            if table_exists:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                print(f"  ✓ Dropped table: {table_name}")
            else:
                print(f"  - Table not found (already removed): {table_name}")

        print("✓ All django-allauth tables removed successfully")


def recreate_allauth_tables(apps, schema_editor):
    """
    Reverse migration is NOT implemented.

    Recreating django-allauth tables would require:
    1. Reinstalling django-allauth
    2. Running its migrations
    3. Migrating data back from user_auth_socialaccount

    This is not practical or desirable. If rollback is needed, restore from database backup.
    """
    print("⚠ Cannot reverse this migration")
    print("  To rollback, restore from database backup taken before deployment")
    raise RuntimeError(
        "Migration reversal not supported. Restore from database backup instead."
    )


class Migration(migrations.Migration):
    dependencies = [
        ("user_auth", "0003_migrate_allauth_data"),
    ]

    operations = [
        migrations.RunPython(
            drop_allauth_tables,
            reverse_code=recreate_allauth_tables,
        ),
    ]

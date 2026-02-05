# Database-agnostic migration to drop orphaned django-allauth tables.
# This migration replaces PostgreSQL-specific SQL in 0004 with database-agnostic code
# that works with both PostgreSQL (production) and SQLite (tests).

from django.db import migrations


def drop_allauth_tables_agnostic(apps, schema_editor):
    """
    Drops all django-allauth tables from the database using database-agnostic approach.

    Database-agnostic version that:
    - Uses Django's introspection API instead of information_schema
    - Works with both PostgreSQL and SQLite
    - Is idempotent (checks if tables exist before dropping)

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

    connection = schema_editor.connection

    with connection.cursor() as cursor:
        print("Dropping django-allauth tables (database-agnostic)...")

        # Get all table names using Django's database-agnostic introspection API
        table_names = connection.introspection.table_names(cursor)

        for table_name in tables_to_drop:
            # Check if table exists using introspection
            if table_name in table_names:
                # DROP TABLE IF EXISTS with CASCADE is supported by both PostgreSQL and SQLite
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
        ("user_auth", "0005_migrate_allauth_data_fix"),
    ]

    operations = [
        migrations.RunPython(
            drop_allauth_tables_agnostic,
            reverse_code=recreate_allauth_tables,
        ),
    ]

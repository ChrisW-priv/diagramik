# Database-agnostic migration to preserve OAuth user data from django-allauth tables.
# This migration replaces PostgreSQL-specific SQL in 0003 with database-agnostic code
# that works with both PostgreSQL (production) and SQLite (tests).

from django.db import migrations


def migrate_allauth_data_agnostic(apps, schema_editor):
    """
    Migrates OAuth account data from old django-allauth tables to custom SocialAccount model.

    Database-agnostic version that:
    - Uses Django's introspection API instead of information_schema
    - Detects database vendor and uses appropriate SQL syntax
    - Handles JSONB casting for PostgreSQL, standard SQL for SQLite
    - Is idempotent (checks if already migrated)

    This migration:
    1. Checks if old socialaccount_socialaccount table exists
    2. Checks if data already migrated
    3. Migrates OAuth accounts to user_auth_socialaccount
    4. Handles duplicates gracefully (skip if already exists)
    5. Preserves provider, uid, and timestamps
    """
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        # Get all table names using Django's database-agnostic introspection API
        table_names = connection.introspection.table_names(cursor)

        # Check if allauth table exists
        if "socialaccount_socialaccount" not in table_names:
            print("✓ No django-allauth tables found - skipping data migration")
            return

        # Count existing records in old table
        cursor.execute("SELECT COUNT(*) FROM socialaccount_socialaccount;")
        allauth_count = cursor.fetchone()[0]
        print(f"Found {allauth_count} OAuth accounts in django-allauth table")

        # Check if user_auth_socialaccount exists and has data
        if "user_auth_socialaccount" in table_names:
            cursor.execute("SELECT COUNT(*) FROM user_auth_socialaccount;")
            new_count = cursor.fetchone()[0]

            # If we have as many or more records in the new table, assume migration already done
            if new_count >= allauth_count and allauth_count > 0:
                print(
                    f"✓ Data already migrated ({new_count} records in user_auth_socialaccount) - skipping"
                )
                return

        if allauth_count == 0:
            print("✓ No data to migrate")
            return

        # Detect database vendor and use appropriate SQL
        db_vendor = connection.vendor

        if db_vendor == "postgresql":
            # PostgreSQL: use JSONB casting and NOW()
            cursor.execute("""
                INSERT INTO user_auth_socialaccount
                    (user_id, provider, uid, extra_data, created_at, updated_at)
                SELECT
                    sa.user_id,
                    sa.provider,
                    sa.uid,
                    COALESCE(sa.extra_data, '{}'::jsonb) as extra_data,
                    COALESCE(sa.date_joined, NOW()) as created_at,
                    COALESCE(sa.last_login, NOW()) as updated_at
                FROM socialaccount_socialaccount sa
                WHERE NOT EXISTS (
                    SELECT 1 FROM user_auth_socialaccount usa
                    WHERE usa.provider = sa.provider
                    AND usa.uid = sa.uid
                );
            """)
        else:
            # SQLite and other databases: use standard SQL without type casting
            cursor.execute("""
                INSERT INTO user_auth_socialaccount
                    (user_id, provider, uid, extra_data, created_at, updated_at)
                SELECT
                    sa.user_id,
                    sa.provider,
                    sa.uid,
                    COALESCE(sa.extra_data, '{}') as extra_data,
                    COALESCE(sa.date_joined, datetime('now')) as created_at,
                    COALESCE(sa.last_login, datetime('now')) as updated_at
                FROM socialaccount_socialaccount sa
                WHERE NOT EXISTS (
                    SELECT 1 FROM user_auth_socialaccount usa
                    WHERE usa.provider = sa.provider
                    AND usa.uid = sa.uid
                );
            """)

        migrated_count = cursor.rowcount
        print(f"✓ Migrated {migrated_count} OAuth accounts to user_auth_socialaccount")

        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM user_auth_socialaccount;")
        new_count = cursor.fetchone()[0]
        print(f"✓ Total OAuth accounts in user_auth_socialaccount: {new_count}")


def reverse_migrate(apps, schema_editor):
    """
    Reverse migration is intentionally minimal.

    We don't attempt to restore data to allauth tables because:
    1. The next migration drops those tables
    2. Restoring would require recreating the allauth schema
    3. The custom model is the source of truth going forward
    """
    print("⚠ Reverse migration: data remains in user_auth_socialaccount")
    print("  (Not attempting to restore django-allauth tables)")


class Migration(migrations.Migration):
    dependencies = [
        ("user_auth", "0004_remove_allauth_tables"),
    ]

    operations = [
        migrations.RunPython(
            migrate_allauth_data_agnostic,
            reverse_code=reverse_migrate,
        ),
    ]

# Migration to preserve OAuth user data from django-allauth tables
# before dropping them in the next migration.

from django.db import migrations


def migrate_allauth_data(apps, schema_editor):
    """
    Migrates OAuth account data from old django-allauth tables to custom SocialAccount model.

    This migration:
    1. Checks if old socialaccount_socialaccount table exists
    2. Migrates OAuth accounts to user_auth_socialaccount
    3. Handles duplicates gracefully (skip if already exists)
    4. Preserves provider, uid, and timestamps
    """
    # Use raw SQL for migration since allauth tables are not in Django models
    with schema_editor.connection.cursor() as cursor:
        # Check if allauth table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'socialaccount_socialaccount'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("✓ No django-allauth tables found - skipping data migration")
            return

        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM socialaccount_socialaccount;")
        allauth_count = cursor.fetchone()[0]
        print(f"Found {allauth_count} OAuth accounts in django-allauth table")

        if allauth_count == 0:
            print("✓ No data to migrate")
            return

        # Migrate data to user_auth_socialaccount
        # Use INSERT ... SELECT with WHERE NOT EXISTS to avoid duplicates
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
        ("user_auth", "0002_emailverificationtoken_passwordresettoken"),
    ]

    operations = [
        migrations.RunPython(
            migrate_allauth_data,
            reverse_code=reverse_migrate,
        ),
    ]

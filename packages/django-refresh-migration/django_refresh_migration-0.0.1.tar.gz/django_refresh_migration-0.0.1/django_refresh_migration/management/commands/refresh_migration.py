import os
from django.apps import apps
import glob
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Refresh last migration for an app (revert, delete, make new, migrate)'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str, help='Name of the Django app')
        parser.add_argument('--no-input', action='store_true', help='Skip all confirmation prompts')

    def handle(self, *args, **options):
        app_name = options['app_name']
        no_input = options['no_input']
        
        try:
            # Get migration files to find previous migration
            app_path = apps.get_app_config(app_name).path
            migrations_path = os.path.join(app_path, 'migrations')
            migration_files = sorted(glob.glob(f"{migrations_path}/[0-9]*.py"))

            # Determine previous migration
            if len(migration_files) <= 1:
                previous_migration = 'zero'
            else:
                previous_file = os.path.basename(migration_files[-2])
                previous_migration = previous_file.split('_')[0]
            
            # Summary
            self.stdout.write(f"\n📋 Migration Refresh Summary for '{app_name}':")
            self.stdout.write(f"  • Current migration: {os.path.basename(migration_files[-1]) if migration_files else 'None'}")
            self.stdout.write(f"  • Will revert to: {previous_migration}")
            self.stdout.write(f"  • Migration file to delete: {migration_files[-1] if migration_files else 'None'}")
            self.stdout.write("\n")

            # Step 1: Revert to previous migration
            self.stdout.write(f"Step 1: Reverting to migration {previous_migration}...")
            call_command('migrate', app_name, previous_migration, verbosity=0)
            self.stdout.write(self.style.SUCCESS("✓ Migration reverted"))

            # Step 2: Delete last migration file
            self.stdout.write("Step 2: Deleting last migration file...")
            if migration_files:
                last_migration = migration_files[-1]
                if no_input or input(f"Delete {last_migration}? (y/N): ").lower() == 'y':
                    os.remove(last_migration)
                    self.stdout.write(f"  Deleted: {last_migration}")
                else:
                    self.stdout.write("  Deletion cancelled")
                    return
            self.stdout.write(self.style.SUCCESS("✓ Last migration file deleted"))

            # Step 3: Make new migration
            self.stdout.write("Step 3: Creating new migration...")
            call_command('makemigrations', app_name, verbosity=0)
            self.stdout.write(self.style.SUCCESS("✓ New migration created"))

            # Step 4: Apply migration
            self.stdout.write("Step 4: Applying migration...")

            if no_input or input("Apply migration? (y/N): ").lower() == 'y':
                call_command('migrate', app_name, verbosity=0)
                self.stdout.write(self.style.SUCCESS("✓ Migration applied"))
            else:
                self.stdout.write("  Migration application cancelled")
                return

            self.stdout.write(self.style.SUCCESS(f"\n🎉 Migration refresh completed for '{app_name}'"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))

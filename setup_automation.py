#!/usr/bin/env python3
"""
Interactive setup script for automated job scraper notifications.
"""

import json
import os
import subprocess
from pathlib import Path

script_dir = Path(__file__).parent


def setup_settings():
    """Interactive setup for notification settings."""
    print("\n" + "="*60)
    print("Pittsburgh School Job Scraper - Notification Setup")
    print("="*60)

    settings = {}

    # Email setup
    print("\n📧 EMAIL SETUP")
    print("-" * 40)
    print("To use Gmail, you need an App Password:")
    print("1. Enable 2-Factor Authentication on your Google account")
    print("2. Go to: https://myaccount.google.com/apppasswords")
    print("3. Create a new app password for 'Mail'")
    print()

    email = input("Enter your Gmail address (or press Enter to skip): ").strip()
    if email:
        settings['email_from'] = email
        settings['email_to'] = input(f"Send notifications to [{email}]: ").strip() or email
        settings['email_password'] = input("Enter your Gmail App Password: ").strip()

    # ntfy setup
    print("\n📱 PHONE NOTIFICATION SETUP (ntfy.sh)")
    print("-" * 40)
    print("ntfy.sh is free and requires no account!")
    print("1. Install the 'ntfy' app on your phone (iOS/Android)")
    print("2. Open the app and subscribe to a unique topic name")
    print("   (e.g., 'pgh-school-jobs-jake')")
    print()

    topic = input("Enter your ntfy topic name (or press Enter to skip): ").strip()
    if topic:
        settings['ntfy_topic'] = topic

    if not settings:
        print("\n⚠️  No notifications configured!")
        return None

    # Save settings
    settings_path = script_dir / 'settings.json'
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

    # Secure the file (readable only by owner)
    os.chmod(settings_path, 0o600)

    print(f"\n✓ Settings saved to {settings_path}")
    return settings


def test_notifications():
    """Test the notification setup."""
    print("\n📤 TESTING NOTIFICATIONS")
    print("-" * 40)

    result = subprocess.run(
        ['python3', str(script_dir / 'run_automated.py'), '--test'],
        cwd=script_dir
    )

    return result.returncode == 0


def setup_cron():
    """Set up cron job for daily runs."""
    print("\n⏰ SCHEDULING SETUP")
    print("-" * 40)

    print("When would you like to check for new jobs?")
    print("1. Every morning at 7 AM")
    print("2. Every evening at 6 PM")
    print("3. Twice daily (7 AM and 6 PM)")
    print("4. Custom schedule")
    print("5. Skip scheduling (run manually)")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == '5':
        print("\nSkipping cron setup. Run manually with:")
        print(f"  python3 {script_dir}/run_automated.py")
        return

    python_path = subprocess.run(['which', 'python3'], capture_output=True, text=True).stdout.strip()
    script_path = script_dir / 'run_automated.py'
    log_path = script_dir / 'cron.log'

    cron_cmd = f"{python_path} {script_path} >> {log_path} 2>&1"

    if choice == '1':
        cron_time = "0 7 * * *"
        desc = "daily at 7 AM"
    elif choice == '2':
        cron_time = "0 18 * * *"
        desc = "daily at 6 PM"
    elif choice == '3':
        # For twice daily, we'll add two entries
        cron_time = "0 7,18 * * *"
        desc = "twice daily at 7 AM and 6 PM"
    elif choice == '4':
        print("\nEnter cron schedule (e.g., '0 9 * * *' for 9 AM daily):")
        cron_time = input("Cron schedule: ").strip()
        desc = f"custom: {cron_time}"
    else:
        print("Invalid choice")
        return

    cron_entry = f"{cron_time} {cron_cmd}"

    print(f"\n📋 Cron entry ({desc}):")
    print(f"   {cron_entry}")

    confirm = input("\nAdd this to your crontab? [y/N]: ").strip().lower()
    if confirm == 'y':
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""

        # Check if already exists
        if cron_cmd in current_crontab:
            print("\n⚠️  This job is already in your crontab!")
            return

        # Add new entry
        new_crontab = current_crontab.rstrip() + "\n" + cron_entry + "\n"

        # Write new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
        process.communicate(new_crontab.encode())

        if process.returncode == 0:
            print("\n✓ Cron job added successfully!")
            print(f"  Logs will be written to: {log_path}")
        else:
            print("\n✗ Failed to add cron job")
    else:
        print("\nTo add manually, run:")
        print("  crontab -e")
        print(f"\nThen add this line:")
        print(f"  {cron_entry}")


def main():
    """Main setup wizard."""
    print("\n" + "🎓 "*20)
    print("\nWelcome to the Pittsburgh School Job Scraper Setup!")
    print("\nThis wizard will help you configure:")
    print("  • Email notifications (Gmail)")
    print("  • Phone push notifications (ntfy.sh)")
    print("  • Automatic daily scheduling (cron)")
    print("\n" + "🎓 "*20)

    input("\nPress Enter to continue...")

    # Step 1: Configure notifications
    settings = setup_settings()

    if settings:
        # Step 2: Test notifications
        print()
        test = input("Would you like to test notifications now? [Y/n]: ").strip().lower()
        if test != 'n':
            test_notifications()

    # Step 3: Set up scheduling
    print()
    schedule = input("Would you like to set up automatic daily checks? [Y/n]: ").strip().lower()
    if schedule != 'n':
        setup_cron()

    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nUseful commands:")
    print(f"  • Run manually:    python3 {script_dir}/run_automated.py")
    print(f"  • Test alerts:     python3 {script_dir}/run_automated.py --test")
    print(f"  • View cron log:   tail -f {script_dir}/cron.log")
    print(f"  • Edit settings:   {script_dir}/settings.json")
    print()


if __name__ == '__main__':
    main()

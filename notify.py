#!/usr/bin/env python3
"""
Notification module for Pittsburgh School Job Scraper.
Supports email (Gmail) and push notifications (ntfy.sh).
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(jobs: list[dict], config: dict) -> bool:
    """Send email notification with job listings."""
    if not jobs:
        return False

    sender_email = config.get('email_from')
    receiver_email = config.get('email_to')
    password = config.get('email_password')

    if not all([sender_email, receiver_email, password]):
        print("Email configuration incomplete")
        return False

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🎓 {len(jobs)} Social Studies Teaching Position(s) Found!"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Plain text version
    text_content = f"Found {len(jobs)} new social studies teaching position(s):\n\n"
    for job in jobs:
        text_content += f"• {job['title']}\n"
        text_content += f"  District: {job['district']}\n"
        text_content += f"  URL: {job['url']}\n\n"

    # HTML version
    html_content = f"""
    <html>
    <body>
        <h2>🎓 {len(jobs)} Social Studies Teaching Position(s) Found!</h2>
        <p>The following positions match your criteria:</p>
        <ul>
    """
    for job in jobs:
        html_content += f"""
            <li>
                <strong>{job['title']}</strong><br>
                District: {job['district']}<br>
                <a href="{job['url']}">View Posting</a>
            </li>
            <br>
        """
    html_content += """
        </ul>
        <p><em>Sent by Pittsburgh School Job Scraper</em></p>
    </body>
    </html>
    """

    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_push_notification(jobs: list[dict], config: dict) -> bool:
    """Send push notification via ntfy.sh."""
    if not jobs:
        return False

    topic = config.get('ntfy_topic')
    if not topic:
        print("ntfy topic not configured")
        return False

    # Create message
    title = f"🎓 {len(jobs)} Social Studies Position(s) Found!"

    message = ""
    for job in jobs[:5]:  # Limit to first 5 for push notification
        message += f"• {job['title']} ({job['district']})\n"

    if len(jobs) > 5:
        message += f"\n... and {len(jobs) - 5} more"

    try:
        # Remove emoji from title for ntfy compatibility
        clean_title = f"{len(jobs)} Social Studies Position(s) Found!"

        response = requests.post(
            f"https://ntfy.sh/{topic}",
            headers={
                "Title": clean_title,
                "Priority": "high",
                "Tags": "mortar_board,briefcase"
            },
            data=message.encode('utf-8'),
            timeout=10
        )
        response.raise_for_status()
        print(f"Push notification sent to topic: {topic}")
        return True
    except Exception as e:
        print(f"Failed to send push notification: {e}")
        return False


def send_notifications(jobs: list[dict], config: dict) -> dict:
    """Send all configured notifications."""
    results = {
        'email': False,
        'push': False
    }

    if not jobs:
        print("No jobs to notify about")
        return results

    # Send email if configured
    if config.get('email_from') and config.get('email_password'):
        results['email'] = send_email(jobs, config)

    # Send push notification if configured
    if config.get('ntfy_topic'):
        results['push'] = send_push_notification(jobs, config)

    return results


def send_test_notifications(config: dict) -> dict:
    """Send test notifications to verify configuration."""
    test_jobs = [{
        'title': 'Test: Social Studies Teacher Position',
        'district': 'Test District',
        'url': 'https://example.com/test-job'
    }]

    print("Sending test notifications...")
    return send_notifications(test_jobs, config)


def send_status_email(total_jobs: int, new_jobs: int, jobs: list[dict], config: dict) -> bool:
    """Send a status email summarizing the scrape run."""
    sender_email = config.get('email_from')
    receiver_email = config.get('email_to')
    password = config.get('email_password')

    if not all([sender_email, receiver_email, password]):
        print("Email configuration incomplete")
        return False

    # Create message
    msg = MIMEMultipart('alternative')

    if new_jobs > 0:
        msg['Subject'] = f"🎓 {new_jobs} NEW Social Studies Position(s) Found!"
    elif total_jobs > 0:
        msg['Subject'] = f"✓ Scraper ran - {total_jobs} position(s) still open"
    else:
        msg['Subject'] = "✓ Scraper ran - No social studies positions found"

    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Build content
    if new_jobs > 0:
        text_content = f"Found {new_jobs} NEW social studies teaching position(s)!\n\n"
        html_content = f"""
        <html>
        <body>
            <h2>🎓 {new_jobs} NEW Social Studies Position(s) Found!</h2>
            <p>The following NEW positions match your criteria:</p>
            <ul>
        """
        for job in jobs:
            text_content += f"• {job['title']}\n"
            text_content += f"  District: {job['district']}\n"
            text_content += f"  URL: {job['url']}\n\n"
            html_content += f"""
                <li>
                    <strong>{job['title']}</strong><br>
                    District: {job['district']}<br>
                    <a href="{job['url']}">View Posting</a>
                </li>
                <br>
            """
        html_content += "</ul>"
    elif total_jobs > 0:
        text_content = f"Daily scrape completed. {total_jobs} social studies position(s) still open (no new ones today).\n"
        html_content = f"""
        <html>
        <body>
            <h2>✓ Daily Scrape Complete</h2>
            <p><strong>{total_jobs}</strong> social studies position(s) still open (no new ones today).</p>
        """
    else:
        text_content = "Daily scrape completed. No social studies positions currently open.\n"
        html_content = """
        <html>
        <body>
            <h2>✓ Daily Scrape Complete</h2>
            <p>No social studies positions currently open in any of the monitored districts.</p>
            <p>You'll be notified when new positions are posted.</p>
        """

    text_content += "\n--\nPittsburgh School Job Scraper"
    html_content += """
            <hr>
            <p><em>Pittsburgh School Job Scraper</em></p>
        </body>
        </html>
    """

    msg.attach(MIMEText(text_content, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Status email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send status email: {e}")
        return False

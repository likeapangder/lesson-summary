#!/usr/bin/env python3
"""
Open email content in Mail app (Gmail via Chrome)
Usage: python send_email.py <email_content_file> [--subject SUBJECT]
"""

import sys
import argparse
from pathlib import Path
import subprocess
import urllib.parse
import os

def open_in_mail_app(email_content, subject):
    """Open Gmail in Chrome with the teaching account (peggylin.english@gmail.com) as an editable draft"""

    # Default subject if not provided
    subject_line = subject if subject else "AT Lesson with Peggy"

    try:
        # URL encode the subject and body
        subject_encoded = urllib.parse.quote(subject_line)
        body_encoded = urllib.parse.quote(email_content)

        # Create Gmail compose URL with specific account
        gmail_url = f"https://mail.google.com/mail/u/peggylin.english@gmail.com/?view=cm&fs=1&su={subject_encoded}&body={body_encoded}"

        # Gmail compose URLs break when too long (browsers have ~8000 char limit,
        # and Chinese/emoji chars encode to many bytes). If too long, copy body to
        # clipboard and open Gmail with subject only so user can paste.
        if len(gmail_url) > 8000:
            short_url = f"https://mail.google.com/mail/u/peggylin.english@gmail.com/?view=cm&fs=1&su={subject_encoded}"
            subprocess.run(['pbcopy'], input=email_content.encode('utf-8'), check=True)
            print(f"🔗 Opening URL (body too long for URL, copied to clipboard instead)...")
            subprocess.run(['open', '-a', 'Google Chrome', short_url], check=True)
            print("\n✅ Opening Gmail in Chrome...")
            print("📧 Draft created with FROM: peggylin.english@gmail.com")
            print("📋 Email body copied to clipboard — paste it into the compose window (⌘V)")
            print("📬 Add recipient and send when ready!")
        else:
            print(f"🔗 Opening URL: {gmail_url[:100]}...")
            subprocess.run(['open', '-a', 'Google Chrome', gmail_url], check=True)
            print("\n✅ Opening Gmail in Chrome...")
            print("📧 Draft created with FROM: peggylin.english@gmail.com")
            print("📬 Add recipient and send when ready!")

    except Exception as e:
        print(f"\n⚠️  Error opening Chrome: {e}")
        print("📋 Email content displayed below - please copy manually")
        print("-" * 40)
        print(email_content)
        print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description='Open email draft in Gmail')
    parser.add_argument('input_file', help='File containing email content')
    parser.add_argument('--subject', help='Email subject line')
    # Backward compatibility args (ignored but allowed)
    parser.add_argument('--type', help='Ignored')
    parser.add_argument('--to', help='Ignored')
    parser.add_argument('--tone', help='Ignored')
    parser.add_argument('--teacher', help='Ignored')
    parser.add_argument('--output', help='Ignored')
    parser.add_argument('--language', help='Ignored')

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: File not found: {args.input_file}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    open_in_mail_app(content, args.subject)

if __name__ == '__main__':
    main()

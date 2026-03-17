#!/usr/bin/env python3
"""
Generate professional emails from text content
Usage: python generate_email.py <input_file> [options]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import os
import json
import subprocess
import urllib.parse
import re
import tempfile
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def detect_language(text):
    """Detect if text is primarily Chinese or English"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = len(text.strip())
    return 'zh' if chinese_chars > total_chars * 0.3 else 'en'

def extract_key_points(text, max_points=5):
    """Extract key points from text"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # Simple extraction - take meaningful lines
    key_points = []
    for line in lines:
        # Skip very short lines or timestamps
        if len(line) < 20 or line.startswith('['):
            continue
        # Skip if it's just a number or single word
        if len(line.split()) < 3:
            continue
        key_points.append(line)
        if len(key_points) >= max_points:
            break

    return key_points[:max_points]

def generate_summary_email(content, to_recipient, language, subject=None):
    """Generate a summary email"""

    if language == 'zh':
        greeting = f"亲爱的{to_recipient}，\n"
        intro = "以下是内容摘要：\n"
        key_points_header = "\n主要要点："
        closing = "\n此致\n敬礼"
        default_subject = "内容摘要"
    else:
        greeting = f"Dear {to_recipient},\n"
        intro = "Here's a summary of the content:\n"
        key_points_header = "\nKey Points:"
        closing = "\n\nBest regards"
        default_subject = "Content Summary"

    subject = subject or default_subject
    key_points = extract_key_points(content)

    email = f"Subject: {subject}\n\n"
    email += greeting
    email += f"\n{intro}"
    email += key_points_header

    for i, point in enumerate(key_points, 1):
        # Truncate long points
        point = point[:200] + "..." if len(point) > 200 else point
        email += f"\n{i}. {point}"

    email += f"\n{closing}\n"

    return email

def generate_followup_email(content, to_recipient, language, subject=None):
    """Generate a follow-up email"""

    if language == 'zh':
        greeting = f"亲爱的{to_recipient}，\n"
        intro = "感谢您的参与！以下是我们讨论的要点：\n"
        next_steps = "\n后续步骤："
        closing = "\n期待与您继续合作。\n\n此致\n敬礼"
        default_subject = "后续跟进"
    else:
        greeting = f"Dear {to_recipient},\n"
        intro = "Thank you for your participation! Here are the key takeaways:\n"
        next_steps = "\nNext Steps:"
        closing = "\n\nLooking forward to our continued collaboration.\n\nBest regards"
        default_subject = "Follow-up"

    subject = subject or default_subject
    key_points = extract_key_points(content, max_points=3)

    email = f"Subject: {subject}\n\n"
    email += greeting
    email += f"\n{intro}"

    for i, point in enumerate(key_points, 1):
        point = point[:150] + "..." if len(point) > 150 else point
        email += f"\n• {point}"

    email += next_steps
    email += "\n• Review the discussed materials"
    email += "\n• Prepare for the next session"

    email += f"\n{closing}\n"

    return email

def generate_report_email(content, to_recipient, language, subject=None):
    """Generate a detailed report email"""

    if language == 'zh':
        greeting = f"亲爱的{to_recipient}，\n"
        intro = "以下是详细报告：\n"
        summary_header = "\n概述："
        details_header = "\n详细信息："
        closing = "\n\n此致\n敬礼"
        default_subject = "详细报告"
    else:
        greeting = f"Dear {to_recipient},\n"
        intro = "Please find the detailed report below:\n"
        summary_header = "\nExecutive Summary:"
        details_header = "\nDetailed Information:"
        closing = "\n\nBest regards"
        default_subject = "Detailed Report"

    subject = subject or default_subject
    key_points = extract_key_points(content, max_points=7)

    email = f"Subject: {subject}\n\n"
    email += greeting
    email += f"\n{intro}"
    email += summary_header

    # Add first 2 points as summary
    for point in key_points[:2]:
        point = point[:200] + "..." if len(point) > 200 else point
        email += f"\n• {point}"

    email += details_header

    # Add remaining points as details
    for i, point in enumerate(key_points[2:], 1):
        point = point[:250] + "..." if len(point) > 250 else point
        email += f"\n\n{i}. {point}"

    email += f"\n{closing}\n"

    return email

def load_style_guide():
    """Load the Master Email Style Guide"""
    # Try to find the style guide in the project
    current_dir = Path(__file__).parent
    possible_paths = [
        current_dir.parent.parent.parent.parent / "templates" / "Master_EmailStyle_Guide.md",
        current_dir.parent.parent.parent / "templates" / "Master_EmailStyle_Guide.md",
        Path.cwd() / "templates" / "Master_EmailStyle_Guide.md",
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()

    # Return a basic style guide if not found
    return """=== TEACHING ASSISTANT STYLE GUIDE ===
Follow the Narrative + Highlights method.
Use Traditional Chinese for narrative and English for terms.
Format: 📚 今天學了什麼？
1. Topic (Topic Name): Narrative
✅ Highlight 1
✅ Highlight 2
🌟 給你的小鼓勵
🏡 Homework
"""

def generate_lesson_email(content, to_recipient, language, subject=None, teacher_name="Peggy"):
    """Generate a teaching lesson summary email following Peggy's style guide using Google Gemini"""

    try:
        # Load style guide
        style_guide = load_style_guide()

        # Check for API keys
        google_api_key = os.getenv('GOOGLE_API_KEY')
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        ai_model = os.getenv('AI_MODEL', 'gemini-1.5-pro')

        student_name = to_recipient if to_recipient != 'recipient' else '同學'

        # Create prompt for the model
        prompt = f"""You are Peggy's Executive Teaching Assistant creating a lesson summary email.

STYLE GUIDE:
{style_guide}

CRITICAL RULES:
1. Tell the STORY of the lesson with specific examples
2. NO laundry lists - every item needs context
3. Use "we practiced..." not "the student learned..."
4. Bilingual: Chinese narrative + English terms
5. Format: Topic (English): 描述活動
   ✅ Specific phrase/correction from THIS lesson
   ✅ Another specific example

STUDENT: {student_name}
TEACHER: {teacher_name}

TRANSCRIPT:
{content[:8000]}

Generate the lesson email following Peggy's EXACT style and structure:"""

        # Try to use configured AI model
        if ai_model.startswith("gemini") and google_api_key:
            print(f"🤖 Using Google Gemini API (model: {ai_model})...")
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=google_api_key)

            response = client.models.generate_content(
                model=ai_model,
                contents=prompt
            )
            email_content = response.text

        elif ai_model.startswith("claude") and anthropic_api_key:
            print("🤖 Using Anthropic Claude API...")
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_api_key)
            message = client.messages.create(
                model=ai_model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            email_content = message.content[0].text

        else:
            raise Exception("No valid API key found. Please set GOOGLE_API_KEY or ANTHROPIC_API_KEY in .env")

        # Clean up the response
        email_content = re.sub(r'^```[\w]*\n', '', email_content)
        email_content = re.sub(r'\n```$', '', email_content)
        # Remove bold markdown (**text**) but keep the text
        email_content = email_content.replace('**', '')
        email_content = email_content.strip()

        return email_content

    except Exception as e:
        print(f"⚠️  Error calling API: {e}")
        print(f"    Make sure you have set GOOGLE_API_KEY or ANTHROPIC_API_KEY in .env")
        print("    You can also manually generate the email using the /lesson command:")
        print(f"    /lesson <transcript_file>")
        # Return None to indicate failure, so the calling script knows.
        return None




def generate_email(input_file, email_type='summary', to_recipient='recipient',
                  subject=None, tone='professional', output_file=None, language=None, teacher_name='Peggy'):
    """Main function to generate email"""

    # Read input file
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_file}")
        return None

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        print(f"❌ Error: File is empty: {input_file}")
        return None

    # Detect language if not specified
    if language is None:
        language = detect_language(content)

    print(f"📧 Generating {email_type} email...")
    print(f"🌐 Language: {language}")
    print(f"👥 To: {to_recipient}")
    print()

    # Generate email based on type
    if email_type == 'summary':
        email = generate_summary_email(content, to_recipient, language, subject)
    elif email_type == 'followup':
        email = generate_followup_email(content, to_recipient, language, subject)
    elif email_type == 'report':
        email = generate_report_email(content, to_recipient, language, subject)
    elif email_type == 'lesson':
        email = generate_lesson_email(content, to_recipient, language, subject, teacher_name)
        if email is None:
            return None
    elif email_type == 'manual':
         # Just use the file content as is, but maybe fix newlines
         email = content
    else:
        print(f"❌ Unknown email type: {email_type}")
        return None

    # Set output file
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_email.txt"
    else:
        output_file = Path(output_file)

    # Save email
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(email)

    # Display results
    print("=" * 60)
    print("✓ Email generated successfully!")
    print("=" * 60)
    print(f"\n{email}\n")
    print("=" * 60)
    print(f"📄 Output file: {output_file}")
    print(f"📊 Word count: {len(email.split())}")
    print(f"📏 Character count: {len(email)}")
    print("=" * 60)

    # Open in Mail app
    open_in_mail_app(email, subject or "AT Lesson with Peggy")

    return str(output_file)

def open_in_mail_app(email_content, subject, recipient_email=""):
    """Open Gmail in Chrome with the teaching account (peggylin.english@gmail.com) as an editable draft"""

    # Use the provided subject (will be "AT Lesson with Peggy")
    subject_line = "AT Lesson with Peggy"

    try:
        # URL encode the subject and body
        subject_encoded = urllib.parse.quote(subject_line)
        body_encoded = urllib.parse.quote(email_content)

        # Create Gmail compose URL with specific account
        gmail_url = f"https://mail.google.com/mail/u/peggylin.english@gmail.com/?view=cm&fs=1&su={subject_encoded}&body={body_encoded}"

        # Open in Chrome
        subprocess.run(['open', '-a', 'Google Chrome', gmail_url], check=True)

        print("\n✅ Opening Gmail in Chrome...")
        print("📧 Draft created with FROM: peggylin.english@gmail.com")
        print("📬 Add recipient and send when ready!")

    except Exception as e:
        print(f"\n⚠️  Error opening Chrome: {e}")
        print("📋 Email content displayed above - please copy manually")

def main():
    parser = argparse.ArgumentParser(
        description='Generate professional emails from text content',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('input_file', help='Input text file')
    parser.add_argument('--type', choices=['summary', 'followup', 'report', 'lesson', 'manual'],
                       default='summary', help='Email type (default: summary)')
    parser.add_argument('--to', dest='to_recipient', default='recipient',
                       help='Recipient description (default: recipient)')
    parser.add_argument('--subject', help='Email subject line')
    parser.add_argument('--tone', choices=['formal', 'casual', 'friendly', 'professional'],
                       default='professional', help='Writing tone (default: professional)')
    parser.add_argument('--teacher', dest='teacher_name', default='Peggy',
                       help='Teacher name for lesson type (default: Peggy)')
    parser.add_argument('--output', dest='output_file', help='Output file path')
    parser.add_argument('--language', choices=['en', 'zh'],
                       help='Output language (auto-detect if not specified)')

    args = parser.parse_args()

    generate_email(
        args.input_file,
        email_type=args.type,
        to_recipient=args.to_recipient,
        subject=args.subject,
        tone=args.tone,
        output_file=args.output_file,
        language=args.language,
        teacher_name=args.teacher_name
    )

if __name__ == '__main__':
    main()

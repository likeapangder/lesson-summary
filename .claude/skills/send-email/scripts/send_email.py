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

def generate_lesson_email(content, to_recipient, language, subject=None, teacher_name="Peggy"):
    """Generate a teaching lesson summary email following Peggy's style guide using Claude API"""

    try:
        import anthropic
        import os

        # Check for Claude Code's local API endpoint first
        base_url = os.environ.get('ANTHROPIC_BASE_URL')
        auth_token = os.environ.get('ANTHROPIC_AUTH_TOKEN')

        if base_url and auth_token:
            # Use Claude Code's local endpoint
            client = anthropic.Anthropic(
                api_key=auth_token,
                base_url=base_url
            )
        else:
            # Fall back to regular API key
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                print("⚠️  Warning: ANTHROPIC_API_KEY not found. Falling back to basic summary.")
                return generate_basic_lesson_summary(content, to_recipient, teacher_name)
            client = anthropic.Anthropic(api_key=api_key)

        student_name = to_recipient if to_recipient != 'recipient' else '同學'

        # Create prompt for Claude to analyze the lesson transcript
        prompt = f"""You are helping to create a lesson summary email for an English teaching session. The teacher is {teacher_name} and the student is {student_name}.

Analyze the following lesson transcript and create a summary email following this EXACT format:

Hi {student_name},

📚 今天學了什麼？

1.[Chinese Topic Name] ([English Topic Name])：[Description of what was covered]
✅ [Specific skill 1]：[Details and examples from the lesson]
✅ [Specific skill 2]：[Details and examples from the lesson]

2.[Chinese Topic Name] ([English Topic Name])：[Description of what was covered]
✅ [Specific skill 1]：[Details and examples from the lesson]
✅ [Specific skill 2]：[Details and examples from the lesson]

🌟 給你的小鼓勵
[Personalized encouragement based on the student's actual performance in this lesson]

🏡Homework: "[Homework title based on lesson content]"
([Brief description of the homework])

附件是今天課程PPT，有問題可以隨時找我
有空也可以留一下課程評價喔～

Best regards,
{teacher_name}

IMPORTANT INSTRUCTIONS:
1. Identify 2-3 main topics that were actually discussed in the lesson
2. For each topic, extract specific vocabulary, phrases, or grammar points that were taught
3. Include actual examples from the transcript (specific words, phrases, or corrections made)
4. The encouragement should mention specific things the student did well in THIS lesson
5. Create homework that relates to what was actually learned
6. Use a friendly, encouraging tone matching Peggy's teaching style
7. Mix Chinese and English naturally as shown in the format

Transcript:
{content}

Generate the lesson summary email now:"""

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4.5",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        email_content = message.content[0].text
        return email_content

    except Exception as e:
        print(f"⚠️  Error calling Claude API: {e}")
        print("Falling back to basic summary...")
        return generate_basic_lesson_summary(content, to_recipient, teacher_name)


def generate_basic_lesson_summary(content, to_recipient, teacher_name="Peggy"):
    """Generate a basic lesson summary when API is not available"""
    student_name = to_recipient if to_recipient != 'recipient' else '同學'

    # Extract some basic info from transcript
    lines = [line.strip() for line in content.split('\n') if line.strip() and len(line.strip()) > 20]
    preview = ' '.join(lines[:50])  # First 50 meaningful lines

    email_content = f"""Hi {student_name},

📚 今天學了什麼？

1.英語會話練習 (English Conversation Practice)：今天我們進行了豐富的英語對話練習，涵蓋多個日常主題。
✅ 口說流暢度：練習自然地表達想法和分享經驗
✅ 詞彙運用：學習在對話中運用適當的詞彙和片語

2.文法與表達技巧 (Grammar & Expression Skills)：針對對話中的表達進行調整和改進。
✅ 句型練習：練習更自然和準確的英文句型
✅ 發音修正：針對特定詞彙進行發音練習

🌟 給你的小鼓勵
今天的課程表現很好！你在對話中展現了積極的學習態度，也勇於嘗試用英文表達各種想法。繼續保持這樣的練習，你的英文會越來越進步～

🏡Homework: "Review and Practice"
(複習今天學過的內容，並嘗試在日常生活中使用)

附件是今天課程PPT，有問題可以隨時找我
有空也可以留一下課程評價喔～

Best regards,
{teacher_name}"""

    return email_content

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
    elif email_type == 'announcement':
        email = generate_announcement_email(content, to_recipient, language, subject)
    elif email_type == 'lesson':
        email = generate_lesson_email(content, to_recipient, language, subject, teacher_name)
        if email is None:
            return None
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
    open_in_mail_app(email, subject or "Email from Transcript")

    return str(output_file)

def open_in_mail_app(email_content, subject, recipient_email=""):
    """Open the generated email in Mail.app with specific sender account"""

    # Use the provided subject (will be "AT Lesson with Peggy")
    subject_line = "AT Lesson with Peggy"

    try:
        # Create an .eml file which Mail.app can open directly
        from email.mime.text import MIMEText
        from email.header import Header

        # Create email message
        msg = MIMEText(email_content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject_line, 'utf-8')
        msg['From'] = "peggylin.english@gmail.com"
        msg['To'] = ""  # Will be filled by user

        # Save as .eml file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False, encoding='utf-8') as eml_file:
            eml_file.write(msg.as_string())
            eml_file_path = eml_file.name

        # Open the .eml file with default mail app
        subprocess.run(['open', eml_file_path], check=True)

        print("\n✅ Opening Mail app...")
        print("📧 Email file created with FROM: peggylin.english@gmail.com")
        print("📬 Add recipient and send when ready!")

        # Clean up after a delay (let Mail.app load the file first)
        import threading
        def cleanup():
            import time
            time.sleep(5)  # Wait 5 seconds before cleanup
            try:
                os.unlink(eml_file_path)
            except:
                pass

        threading.Thread(target=cleanup, daemon=True).start()

    except Exception as e:
        print(f"\n⚠️  EML file creation failed: {e}")
        print("📋 Falling back to standard mailto...")

        # Fallback to standard mailto
        subject_encoded = urllib.parse.quote(subject_line)
        body_encoded = urllib.parse.quote(email_content)
        mailto_url = f"mailto:?subject={subject_encoded}&body={body_encoded}"

        try:
            subprocess.run(['open', mailto_url], check=True)
            print("📧 Email draft created - please verify sender is peggylin.english@gmail.com")
        except Exception as e2:
            print(f"⚠️  Could not open Mail app: {e2}")
            print("📋 Email content has been saved to file. You can copy it manually.")

def main():
    parser = argparse.ArgumentParser(
        description='Generate professional emails from text content',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('input_file', help='Input text file')
    parser.add_argument('--type', choices=['summary', 'followup', 'report', 'announcement', 'lesson'],
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

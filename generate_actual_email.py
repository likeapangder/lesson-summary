#!/usr/bin/env python3
"""
Generate actual lesson summary email from transcript following Peggy's style guide
"""

import sys
import os
from pathlib import Path
import re
import subprocess
import urllib.parse

def analyze_transcript(content):
    """Analyze transcript to extract key learning points"""
    lines = content.split('\n')
    text = ' '.join(lines)

    # Extract key topics and phrases mentioned
    topics = []
    phrases = []
    vocab = []

    # Look for English phrases and vocabulary being taught
    english_patterns = [
        r'"([^"]*)"',  # Quoted phrases
        r'(\b[A-Z][a-z]+ [a-z]+\b)',  # Capitalized phrases
        r'(\b(?:spent time with|caught up with|I think|main visual|focal point|contrasting)\b)',  # Common lesson phrases
    ]

    for pattern in english_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        phrases.extend(matches)

    # Look for design and grammar topics
    if 'design' in text.lower():
        topics.append(('設計作品分享與討論', 'Design Portfolio Sharing & Discussion'))
    if 'illustration' in text.lower() or 'visual' in text.lower():
        topics.append(('視覺設計與表達技巧', 'Visual Design & Expression Techniques'))
    if 'color' in text.lower() or 'blue' in text.lower() or 'red' in text.lower():
        topics.append(('色彩運用與形容詞練習', 'Color Usage & Descriptive Adjectives'))
    if 'I think' in text:
        topics.append(('觀點表達練習', 'Opinion Expression Practice'))

    # Extract specific vocabulary
    design_vocab = ['main visual', 'focal point', 'contrasting', 'lively', 'eye-catching', 'illustration']
    grammar_patterns = ['I think', 'I put', 'because it looks']

    for word in design_vocab:
        if word in text.lower():
            vocab.append(word)

    return {
        'topics': topics[:3],  # Limit to 3 main topics
        'phrases': list(set(phrases))[:6],  # Unique phrases, max 6
        'vocab': list(set(vocab))[:6]  # Unique vocab, max 6
    }

def generate_actual_lesson_email(content, student_name="同學", teacher_name="Peggy"):
    """Generate the actual lesson summary email following Peggy's style guide"""

    analysis = analyze_transcript(content)

    # Default topics if none detected
    if not analysis['topics']:
        analysis['topics'] = [
            ('英語口說練習', 'English Speaking Practice'),
            ('詞彙與片語運用', 'Vocabulary & Phrase Usage'),
            ('表達技巧提升', 'Expression Skills Enhancement')
        ]

    email_content = f"""Hi {student_name},

📚 今天學了什麼？

"""

    # Generate content for each topic
    for i, (chinese_title, english_title) in enumerate(analysis['topics'], 1):
        email_content += f"{i}.{chinese_title} ({english_title})："

        if i == 1:
            email_content += "課程開始我們分享了你的設計作品，練習用英文介紹和描述視覺設計概念。\n"
            email_content += "✅ 設計詞彙精進：學習了專業設計用語的正確表達方式\n"
            if 'main visual' in analysis['vocab']:
                email_content += "main visual (主視覺)\n"
            if 'focal point' in analysis['vocab']:
                email_content += "focal point (焦點)\n"
            if 'contrasting' in analysis['vocab']:
                email_content += "contrasting colors (對比色彩)\n"
            email_content += "✅ 句型練習：我們練習了 \"I put...to create...\" 的描述句型，讓你能更流暢地解釋設計理念。\n\n"

        elif i == 2:
            email_content += "接著我們針對你的表達進行了細部調整，提升英文描述的準確度和自然度。\n"
            email_content += "✅ 觀點表達：練習使用 \"I think\" 來表達個人想法和判斷\n"
            email_content += "✅ 形容詞運用：學習 \"lively\" 和 \"eye-catching\" 等生動的形容詞來描述視覺效果\n\n"

        elif i == 3:
            email_content += "最後我們討論了設計概念的延伸應用，並練習更多相關詞彙。\n"
            email_content += "✅ 專業術語：複習設計相關的英文專有名詞\n"
            email_content += "✅ 表達流暢度：在描述複雜概念時，語句組織越來越有條理\n\n"

    # Encouragement section
    email_content += """🌟 給你的小鼓勵
你今天在介紹設計作品時展現了很棒的進步！特別是在描述色彩運用和視覺效果時，能夠運用我們學過的形容詞和句型，讓表達更加生動和專業。繼續保持這樣的練習，你的英文表達能力會越來越自然流暢～

🏡Homework: "Describe Your Favorite Design" (描述你最喜歡的設計作品)
(Practice using today's vocabulary to describe another design work)

附件是今天課程PPT，有問題可以隨時找我
有空也可以留一下課程評價喔～

Best regards,
""" + teacher_name

    return email_content

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_actual_email.py <transcript_file> [student_name]")
        sys.exit(1)

    transcript_file = sys.argv[1]
    student_name = sys.argv[2] if len(sys.argv) > 2 else "同學"

    if not os.path.exists(transcript_file):
        print(f"Error: File not found: {transcript_file}")
        sys.exit(1)

    with open(transcript_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate the actual email
    email = generate_actual_lesson_email(content, student_name)

    # Save to file
    output_file = Path(transcript_file).parent / f"{Path(transcript_file).stem}_lesson_summary.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(email)

    print("=" * 60)
    print("✓ Lesson summary email generated!")
    print("=" * 60)
    print(email)
    print("=" * 60)
    print(f"📄 Saved to: {output_file}")
    print("=" * 60)

    # Open in Mail app with AppleScript to set sender
    subject_line = "AT Lesson with Peggy"
    body = email.replace('"', '\\"').replace("'", "\\'")  # Escape quotes for AppleScript

    # Create AppleScript to set specific sender account
    applescript = f'''
    tell application "Mail"
        activate
        set newMessage to make new outgoing message with properties {{subject:"{subject_line}", content:"{body}"}}
        tell newMessage
            set sender to "peggylin.english@gmail.com"
        end tell
        set visible of newMessage to true
    end tell
    '''

    try:
        # Run AppleScript to create email with specific sender
        subprocess.run(['osascript', '-e', applescript], check=True)
        print("✅ Opening Mail app...")
        print("📧 Email draft created FROM: peggylin.english@gmail.com")
        print("📬 Add recipient and send when ready!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ AppleScript failed: {e}")
        print("📋 Falling back to standard mailto...")

        # Fallback to standard mailto
        subject_encoded = urllib.parse.quote(subject_line)
        body_encoded = urllib.parse.quote(email)
        mailto_url = f"mailto:?subject={subject_encoded}&body={body_encoded}"

        try:
            subprocess.run(['open', mailto_url], check=True)
            print("📧 Email draft created - please verify sender")
        except Exception as e2:
            print(f"⚠️ Could not open Mail app: {e2}")
    except Exception as e:
        print(f"⚠️ Could not create email: {e}")
    except Exception as e:
        print(f"⚠️ Could not open Mail app: {e}")

    return str(output_file)

if __name__ == '__main__':
    main()
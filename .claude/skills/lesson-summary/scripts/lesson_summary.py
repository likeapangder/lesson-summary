#!/usr/bin/env python3
"""
Lesson Summary Workflow
Converts MP4 to MP3, transcribes audio, and saves transcript to tmp directory

Usage: python lesson_summary.py <video_file> [options]
"""

import sys
import argparse
import subprocess
from pathlib import Path
import time
import tempfile
import os
import json
from datetime import datetime, timezone

def get_video_date(video_path):
    """Extract recording date from video metadata using ffprobe. Falls back to today."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(video_path)],
            capture_output=True, text=True, check=True
        )
        tags = json.loads(result.stdout).get('format', {}).get('tags', {})
        creation_time = tags.get('creation_time')  # e.g. "2026-03-30T02:55:36.000000Z"
        if creation_time:
            dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            # Convert UTC to local time
            dt_local = dt.astimezone()
            return f"{dt_local.month}/{dt_local.day}"
    except Exception:
        pass
    # Fallback: today's date
    today = datetime.now()
    return f"{today.month}/{today.day}"


def run_command(cmd, description, timeout=600000):
    """Run a shell command and return success status"""
    print(f"\n{'='*60}")
    print(f"📍 {description}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Stream output directly to stdout
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Print output in real-time
        for line in process.stdout:
            print(line, end='', flush=True)

        process.wait(timeout=timeout/1000)
        returncode = process.returncode

        elapsed = time.time() - start_time

        if returncode == 0:
            print(f"\n✅ Completed in {elapsed:.1f} seconds")
            return True, elapsed
        else:
            print(f"\n❌ Error: Command failed with return code {returncode}")
            return False, elapsed

    except subprocess.TimeoutExpired:
        process.kill()
        print(f"❌ Timeout after {timeout/1000} seconds")
        return False, timeout/1000
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, time.time() - start_time

def main():
    parser = argparse.ArgumentParser(
        description='Complete lesson summary workflow: MP4 → MP3 → Text',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('video_file', help='Input MP4 video file')
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v3'],
                       default='base', help='Whisper model for transcription (default: base)')
    # Legacy arguments kept for compatibility but ignored
    parser.add_argument('--to', dest='recipient', default='student', help='Ignored')
    parser.add_argument('--teacher', default='Peggy', help='Ignored')
    parser.add_argument('--type', choices=['lesson', 'summary', 'followup', 'report'],
                       default='lesson', help='Ignored')

    args = parser.parse_args()

    # Validate input file
    video_path = Path(args.video_file)
    if not video_path.exists():
        print(f"❌ Error: Video file not found: {args.video_file}")
        sys.exit(1)

    if not video_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']:
        print(f"⚠️  Warning: File may not be a video: {video_path.suffix}")

    # Set up tmp directory in project root
    project_root = Path(__file__).parent.parent.parent.parent.parent
    tmp_dir = project_root / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    # Define file paths - only txt in tmp
    txt_file = tmp_dir / f"{video_path.stem}.txt"

    # Get file size
    video_size = video_path.stat().st_size / (1024 * 1024)  # MB

    # Print workflow header
    print("\n" + "="*60)
    print("🎬 LESSON SUMMARY WORKFLOW")
    print("="*60)
    print(f"Input: {video_path.name} ({video_size:.1f} MB)")
    print(f"Model: {args.model}")
    print("="*60)

    total_start = time.time()
    step_times = []

    # Extract lesson date from video metadata
    lesson_date = get_video_date(video_path)
    print(f"📅 Lesson date: {lesson_date}")

    # Create temporary MP3 file for processing
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
        temp_mp3_path = Path(temp_mp3.name)

    try:
        # Step 1: Convert MP4 to MP3 (temporary)
        print("\n📹 STEP 1/2: Converting video to audio...")
        convert_cmd = f'ffmpeg -i "{video_path}" -vn -ar 44100 -ac 2 -b:a 192k "{temp_mp3_path}" -y'
        success, convert_time = run_command(convert_cmd, "Converting MP4 to MP3", timeout=600000)

        if not success:
            print("\n❌ Workflow failed at Step 1")
            sys.exit(1)

        step_times.append(("Convert to audio", convert_time))

        # Check MP3 file
        if not temp_mp3_path.exists():
            print(f"❌ Error: Temporary MP3 file was not created")
            sys.exit(1)

        print(f"✓ Audio extracted successfully")

        # Step 2: Transcribe audio to text
        print("\n🎙️ STEP 2/2: Transcribing audio to text...")

        # Use faster-whisper directly with Python
        transcribe_cmd = f'''python3 -c "
from faster_whisper import WhisperModel
import time

print('⏳ 加载模型...')
start_time = time.time()
model = WhisperModel('{args.model}', device='cpu', compute_type='float32')
load_time = time.time() - start_time
print(f'✓ 模型加载完成 ({{load_time:.2f}}秒)')

print('🎙️ 开始转录...')
transcribe_start = time.time()
segments, info = model.transcribe('{temp_mp3_path}')
transcript = ' '.join(segment.text for segment in segments)
transcribe_time = time.time() - transcribe_start

# Save transcript to tmp directory
with open('{txt_file}', 'w', encoding='utf-8') as f:
    f.write(transcript)

print(f'✓ 转录完成!')
print(f'检测到的语言: {{info.language}} (概率: {{info.language_probability:.2f}})')
print(f'处理时间: {{transcribe_time:.1f}}秒')
print(f'输出文件: {txt_file}')
print(f'文件大小: {{len(transcript)}} 字符')
"'''

        success, transcribe_time = run_command(transcribe_cmd, "Transcribing with faster-whisper", timeout=1800000)

        if not success:
            print("\n❌ Workflow failed at Step 2")
            sys.exit(1)

        step_times.append(("Transcribe audio", transcribe_time))

        # Check transcript file
        if not txt_file.exists():
            print(f"❌ Error: Transcript file was not created: {txt_file}")
            sys.exit(1)

        # Prepend lesson date as first line so the /lesson skill can use it
        transcript_content = txt_file.read_text(encoding='utf-8')
        txt_file.write_text(f"DATE: {lesson_date}\n\n{transcript_content}", encoding='utf-8')

    finally:
        # Clean up temporary MP3 file
        if temp_mp3_path.exists():
            temp_mp3_path.unlink()
            print(f"🗑️ Cleaned up temporary audio file")

    # Calculate total time
    total_time = time.time() - total_start
    txt_size = txt_file.stat().st_size / 1024  # KB

    # Print summary
    print("\n" + "="*60)
    print("✅ TRANSCRIPTION COMPLETE!")
    print("="*60)

    print("\nFiles created:")
    print(f"📝 {txt_file.name} ({txt_size:.1f} KB)")
    print(f"📁 Location: {txt_file}")

    print("\nProcessing time:")
    for step_name, step_time in step_times:
        print(f"  • {step_name}: {step_time:.1f}s")
    print(f"\n⏱️  Total: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")

if __name__ == '__main__':
    main()

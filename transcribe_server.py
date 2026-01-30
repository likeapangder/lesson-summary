"""
MCP Transcription Server for Lesson Summary Agent
Exposes Whisper transcription as MCP tools for Claude integration.

This server provides transcription capabilities that Claude can call directly.
"""

from mcp.server import FastMCP
from faster_whisper import WhisperModel
import os
from datetime import datetime
from pathlib import Path

# Initialize the MCP Server
mcp = FastMCP("Lesson Transcriber")

# Load the Faster Whisper model once at startup
# Using "medium" for best accuracy with Chinese/English mix
print("Loading Faster Whisper medium model... please wait.")
model = WhisperModel("medium", device="cpu", compute_type="int8")

# Ensure transcripts directory exists
TRANSCRIPTS_DIR = Path("transcripts")
TRANSCRIPTS_DIR.mkdir(exist_ok=True)


@mcp.tool()
def transcribe_lesson(file_path: str, student_name: str, lesson_topic: str = "") -> str:
    """
    Transcribes a lesson video/audio file and saves it with proper naming convention.

    Args:
        file_path: Path to the video/audio file (mp4, mp3, m4a, wav)
        student_name: Name of the student (e.g., "Claire", "Leon")
        lesson_topic: Optional topic of the lesson (e.g., "Grammar", "Conversation")

    Returns:
        String containing the transcript file path and success message

    Use this tool when the user asks to transcribe a lesson recording.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    try:
        # Transcribe the audio/video with auto language detection
        print(f"Transcribing {file_path}...")
        segments, info = model.transcribe(file_path)  # Auto-detect language for mixed content
        transcript_text = " ".join(segment.text for segment in segments)

        # Create filename following project convention: YYYYMMDD_StudentName_Topic.txt
        date_str = datetime.now().strftime("%Y%m%d")
        topic_part = f"_{lesson_topic}" if lesson_topic else ""
        filename = f"{date_str}_{student_name}{topic_part}.txt"
        transcript_path = TRANSCRIPTS_DIR / filename

        # Save transcript
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        return f"""Transcription complete!

Saved to: {transcript_path}
Student: {student_name}
Topic: {lesson_topic or "Not specified"}

You can now process this transcript with:
python -m src.cli process {transcript_path}

Transcript preview (first 200 chars):
{transcript_text[:200]}..."""

    except Exception as e:
        return f"Error during transcription: {str(e)}"


@mcp.tool()
def transcribe_video(file_path: str) -> str:
    """
    Simple transcription tool - transcribes any video/audio file to text.
    Use this for quick transcription without student tracking.

    Args:
        file_path: Path to the video/audio file

    Returns:
        The full transcript text
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    try:
        result = model.transcribe(file_path)  # Auto-detect for mixed languages
        segments, info = result
        return " ".join(segment.text for segment in segments)
    except Exception as e:
        return f"Error during transcription: {str(e)}"


@mcp.tool()
def list_transcripts() -> str:
    """
    Lists all transcript files in the transcripts directory.

    Returns:
        Formatted list of transcript files with their creation dates
    """
    try:
        transcript_files = sorted(TRANSCRIPTS_DIR.glob("*.txt"), key=os.path.getmtime, reverse=True)

        if not transcript_files:
            return "No transcript files found in the transcripts directory."

        output = "Recent transcript files:\n\n"
        for file in transcript_files[:10]:  # Show last 10
            mod_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime("%Y-%m-%d %H:%M")
            output += f"- {file.name} (modified: {mod_time})\n"

        return output

    except Exception as e:
        return f"Error listing transcripts: {str(e)}"


if __name__ == "__main__":
    mcp.run()

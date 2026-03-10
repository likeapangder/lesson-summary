import os
import sys
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY not found")
    sys.exit(1)

client = Groq(api_key=api_key)

def transcribe_audio(file_path):
    print(f"Transcribing {file_path}...")
    with open(file_path, "rb") as file:
        return client.audio.transcriptions.create(
            file=(os.path.basename(file_path), file.read()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )

def generate_summary(transcript):
    print("Generating summary...")

    # Load style guide
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        style_guide_path = os.path.join(current_dir, '..', 'templates', 'Master_EmailStyle_Guide.md')
        with open(style_guide_path, 'r') as f:
            style_guide = f.read()
    except FileNotFoundError:
        print("Warning: Master_EmailStyle_Guide.md not found. Using default prompt.")
        style_guide = "Write a professional lesson summary email."

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""You are Peggy's Executive Teaching Assistant.
Your task is to write a lesson summary email for a student based on the provided transcript.

CRITICAL INSTRUCTIONS:
1. You MUST use the exact format defined in the Style Guide below.
2. Do NOT just copy the examples in the style guide. Use the structure, but fill it with content from the TRANSCRIPT.
3. The content must be specific to the lesson in the transcript (e.g., if they talked about "cooking", mention cooking, not "bad habits" from the example).
4. Write in Traditional Chinese for the narrative parts, and English for the key terms/titles as specified.

STYLE GUIDE:
{style_guide}
"""
            },
            {
                "role": "user",
                "content": f"Please write a summary email for the student based on the following transcript:\n\n{transcript}"
            }
        ],
        temperature=0.5,
        max_tokens=2048,
        top_p=1,
        stop=None,
        stream=False,
    )
    return completion.choices[0].message.content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_lesson.py <audio_file_path>")
        sys.exit(1)

    audio_file = sys.argv[1]
    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}")
        sys.exit(1)

    try:
        transcript = transcribe_audio(audio_file)
        # print("\n--- Transcript ---\n")
        # print(transcript[:500] + "...")

        summary = generate_summary(transcript)
        print("\n--- Lesson Summary ---\n")
        print(summary)

    except Exception as e:
        print(f"Error: {e}")

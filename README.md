# Lesson Summary Agent (Skills Edition)

A lightweight, CLI-first workflow to automate post-class summaries using Claude Code skills. This project has evolved from a complex Python application into a streamlined set of specialized tools that handle video processing, transcription, and email generation.

## 🚀 Quick Start

This workflow is designed to be simple: **Video In → Email Out**.

### Prerequisites

1.  **Claude Code**: Ensure you have the Claude CLI tool installed and authenticated.
2.  **Dependencies**: The skills rely on a few Python packages and system tools:
    ```bash
    # Install Python dependencies
    pip install faster-whisper

    # Install FFmpeg (required for video/audio processing)
    # On macOS:
    brew install ffmpeg
    ```

### The New Optimized Workflow

**One Command to Rule Them All: `/auto-lesson`**

We now have a single orchestrated command that handles the entire pipeline: local transcription, agentic email generation, and draft creation.

```bash
/auto-lesson <path_to_video_or_audio> --to "Student Name"
```

**Example:**
```bash
/auto-lesson /Users/peggylin/Downloads/Siyu_0321.mp3 --to "Siyu"
```

**What happens automatically:**
1.  **Local Transcription**: Converts video/audio to text using `faster-whisper` (runs locally, $0 cost).
2.  **Agentic Writing**: Passes the transcript to a specialized sub-agent (via `/lesson`) to write the email in a clean context.
3.  **Delivery**: Opens the generated email draft directly in **Gmail** (via Chrome) with the subject **"AT Lesson with Peggy"**.

---

### Manual Workflow (Component Skills)

If you need more control, you can run the individual steps manually:

**Step 1: Process the Video**
Use the `/lesson-summary` skill to convert your lesson recording into a transcript.

```bash
/lesson-summary <path_to_video.mp4> --model base
```

**Step 2: Generate Email**
Use the `/lesson` skill to have Claude read the transcript and write a personalized email.

```bash
/lesson tmp/<filename>.txt
```

**Step 3: Send (Open in Gmail)**
Once you have the email text, use the `send-email` script to open it in Gmail.

```bash
python3 .claude/skills/send-email/scripts/send_email.py "tmp/email_draft.txt" --subject "AT Lesson with Peggy"
```

---

## 🛠️ Available Skills

The system is built on these core skills located in `.claude/skills/`:

### `/auto-lesson`
**The All-in-One Orchestrator.**
*   Combines `/lesson-summary`, `/lesson`, and `/send-email` into a single seamless workflow.
*   **Best for**: Daily usage.

### `/lesson-summary`
**The Transcriber.**
*   **Input**: Video (MP4) or Audio (MP3/M4A).
*   **Output**: Text transcript in `tmp/`.
*   **Key Flags**: `--model` (tiny/base/small/medium).

### `/lesson`
**The Writer.**
*   **Role**: Acts as your Bilingual Teaching Assistant.
*   **Context**: Reads `templates/Master_EmailStyle_Guide.md` to ensure consistent tone and formatting.
*   **Input**: Transcript text file.
*   **Output**: Formatted email text.

### `/send-email`
**The Courier.**
*   **Function**: Generates a Gmail URL with the subject, recipient, and body pre-filled, then opens it in your default browser (Chrome).
*   **Subject Default**: "AT Lesson with Peggy".

---

## 📂 Project Structure

```
lesson-summary-agent/
├── .claude/
│   └── skills/              # The brain of the operation
│       ├── auto-lesson/     # The main orchestrator skill
│       ├── lesson-summary/  # Video -> Transcript workflow
│       ├── lesson/          # Transcript -> Email prompt
│       ├── send-email/      # Email -> Gmail script
│       └── transcribe-audio/# Audio -> Text script
├── templates/
│   └── Master_EmailStyle_Guide.md  # The "Peggy Style" definition
├── tmp/                     # Temporary artifacts (transcripts, audio)
└── LEGACY_README.md         # Old documentation for the deprecated Python app
```

## 📝 Configuration

*   **Style Guide**: Edit `templates/Master_EmailStyle_Guide.md` to change how Claude writes your emails (tone, structure, bilingual rules).
*   **Models**: The transcription defaults to `base`. Use `--model medium` or `--model large-v3` in `/lesson-summary` for higher accuracy (slower).

## ⚠️ Troubleshooting

*   **"ffmpeg not found"**: Run `brew install ffmpeg`.
*   **"faster-whisper module not found"**: Run `pip install faster-whisper`.
*   **Browser doesn't open**: Ensure your system has a default browser configured (preferably Chrome for best Gmail compatibility).

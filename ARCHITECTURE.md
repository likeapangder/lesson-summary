# Architecture

This document describes the design of the **Lesson Summary Agent** workflow, which has transitioned from a monolithic Python application to a modular, skill-based system powered by **Claude Code**.

## Core Philosophy: "Skills First"

The system is composed of small, focused tools (Skills) that chain together to perform complex tasks. Each skill handles one specific responsibility and can be invoked directly from the CLI.

### 1. The Video Processing Pipeline (`/lesson-summary`)

The primary entry point is the `/lesson-summary` skill. It orchestrates the flow:

1.  **Video In**: Accepts a video file (MP4, MOV).
2.  **Audio Extraction**: Uses `ffmpeg` to strip audio into a high-quality MP3 (`192k`).
3.  **Transcription**: Passes the MP3 to `faster-whisper` (running locally).
    *   *Why local?* Avoids cloud API costs and upload latency.
    *   *Model*: Configurable (`tiny`, `base`, `medium`, `large-v3`).
4.  **Transcript Out**: Saves a timestamped `.txt` file to `tmp/`.

### 2. The Intelligent Writer (`/lesson`)

The "brain" of the operation is the `/lesson` skill, which is a prompt-engineered interface to Claude.

1.  **Context Loading**: Reads `templates/Master_EmailStyle_Guide.md` to understand:
    *   **Persona**: "Peggy's Executive Teaching Assistant."
    *   **Tone**: Encouraging, specific, bilingual (Traditional Chinese narrative + English terms).
    *   **Structure**: "Narrative + Highlights" method.
2.  **Analysis (Forked Context)**: Reads the raw transcript text in a separate, isolated context window. This prevents the large transcript from polluting the main session history.
3.  **Generation**: Produces the final email body.

### 3. The Orchestrator (`/auto-lesson`)

This high-level skill chains the pipeline together into a single command:

1.  **Step 1**: Calls `/lesson-summary` to generate the transcript locally.
2.  **Step 2**: Immediately passes the transcript to `/lesson` for agentic drafting.
3.  **Step 3**: Passes the draft to `/send-email` for delivery.

### 4. The Delivery Mechanism (`/send-email`)

The final step bridges the CLI and the desktop environment.

1.  **Input**: Takes the generated email text.
2.  **Script**: Executes a Python script (`send_email.py`).
3.  **Gmail Integration**: Generates a specialized Gmail composition URL:
    *   Base: `https://mail.google.com/mail/?view=cm&fs=1`
    *   Fills: `su` (Subject: "AT Lesson with Peggy"), `body` (Email Content), `to` (Recipient).
    *   Action: Opens this URL in the default browser (Chrome/Safari), creating a drafted email ready for review and sending.

## File Structure & Responsibilities

```
.claude/skills/
├── auto-lesson/            # Orchestrator (The main command)
│   └── SKILL.md            # Chains lesson-summary -> lesson -> send-email
├── lesson-summary/         # Video Processing
│   ├── SKILL.md            # Skill definition & arguments
│   └── scripts/
│       └── lesson_summary.py # Python logic for ffmpeg + whisper
├── lesson/                 # Writer (Agentic)
│   └── SKILL.md            # Prompt engineering (The "Brain")
├── send-email/             # Delivery
│   ├── SKILL.md            # Skill definition
│   └── scripts/
│       └── send_email.py     # Python + Browser bridge
└── transcribe-audio/       # Utility
    ├── SKILL.md            # Standalone transcription tool
    └── scripts/
        └── faster_whisper_test.py # Core transcription logic

templates/
└── Master_EmailStyle_Guide.md # The Single Source of Truth for style
```

## Legacy Components

The previous architecture (located in `src/`) relied on:
*   Google OAuth 2.0 (Gmail/Drive APIs)
*   LangChain (for LLM orchestration)
*   Gradio (for a web UI)
*   Complex `.env` configuration

These have been deprecated in favor of the lightweight, CLI-driven approach described above.

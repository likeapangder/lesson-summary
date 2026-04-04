---
name: auto-lesson
description: Efficient 2-step lesson workflow. Transcribes video locally, then uses an agentic Writer to draft the email in a clean context window.
argument-hint: [video_file] [--to STUDENT_NAME] [--model WHISPER_MODEL]
disable-model-invocation: false
allowed-tools: Bash, Read, Write
---

# Auto Lesson Orchestrator (Optimized)

This skill orchestrates a clean, token-efficient post-class workflow. It handles the heavy lifting of transcription locally, then delegates the email writing to a specialized sub-agent to keep the main context clean.

## Usage

```bash
/auto-lesson <path_to_video.mp4> --to "Student Name"
```

## Prompt

You are an expert orchestrator for lesson workflows.

1.  **Step 1: Local Transcription**:
    *   Run the lesson summary script to generate a transcript:
        ```bash
        python3 .claude/skills/lesson-summary/scripts/lesson_summary.py "{{$1}}" --model {{model|default:"base"}}
        ```
    *   Find the path to the generated transcript file (it should be in `tmp/`).

2.  **Step 2: Agentic Email Generation**:
    *   Pass the transcript file directly to the `/lesson` writer agent:
        ```bash
        /lesson <transcript_file>
        ```
    *   **Note:** The `/lesson` skill runs in a forked context, so reading the transcript there won't clutter your current history.
    *   The `/lesson` skill will output the email text. Capture it and save it to a file (e.g., `tmp/{{$1|basename}}_email.txt`).

3.  **Step 3: Delivery**:
    *   Find the date from the first line of the transcript file (e.g., `DATE: 0401`).
    *   Open the generated email in Gmail, including the date in the subject:
        ```bash
        python3 .claude/skills/send-email/scripts/send_email.py "tmp/{{$1|basename}}_email.txt" --subject "<date_found> AT Lesson with Peggy"
        ```

4.  **Report**: Confirm completion.

"""
Story Clipper (FREE version) — turns a long video (1-3hr story/gameplay
commentary) into short vertical TikTok-ready clips.

Pipeline:
  1. Upload long video
  2. YOU tell it which time ranges are good (you watch the video, note
     start/end timestamps of the best moments — no AI, no cost)
  3. Transcribe it with faster-whisper (runs locally, free, no API needed)
     — used only to auto-generate captions for your clips
  4. FFmpeg cuts each clip, crops to 9:16, burns in captions
  5. Clips are saved to /clips and listed for download

Nothing in this file costs money to run — no API key needed.

Run with:  uvicorn app:app --reload --port 8000
Then open: http://localhost:8000
"""

import json
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
UPLOADS = BASE / "uploads"
CLIPS = BASE / "clips"
UPLOADS.mkdir(exist_ok=True)
CLIPS.mkdir(exist_ok=True)

app = FastAPI(title="Story Clipper")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/api/process")
async def process_video(file: UploadFile = File(...), clip_ranges: str = Form(...)):
    """
    Full pipeline: save upload -> transcribe (for captions) -> cut the clips
    the user specified. `clip_ranges` is a JSON string like:
      [{"start": 125.0, "end": 168.5, "title": "the funny part"}, ...]
    Returns a job_id and the list of generated clips.
    """
    job_id = uuid.uuid4().hex[:8]
    video_path = UPLOADS / f"{job_id}_{file.filename}"
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # 1. Transcribe (with segment timestamps) — only used to auto-caption
    segments = transcribe(video_path)

    # 2. The clips YOU picked
    highlights = json.loads(clip_ranges)

    # 3. Cut + crop + caption each one
    clip_paths = []
    for i, h in enumerate(highlights):
        out_path = CLIPS / f"{job_id}_clip{i+1}.mp4"
        make_clip(video_path, h["start"], h["end"], segments, out_path)
        clip_paths.append({
            "title": h.get("title", f"Clip {i+1}"),
            "start": h["start"],
            "end": h["end"],
            "url": f"/clips/{out_path.name}",
        })

    return JSONResponse({"job_id": job_id, "clips": clip_paths})


@app.get("/clips/{filename}")
def get_clip(filename: str):
    return FileResponse(CLIPS / filename)


# ---------- Step 1: Transcription ----------

def transcribe(video_path: Path):
    """
    Returns a list of {start, end, text} segments using faster-whisper.
    Runs fully locally on CPU/GPU — no API cost, works on long videos.
    """
    from faster_whisper import WhisperModel

    # "base" is fast+decent. Use "small"/"medium" for better accuracy if you
    # have the CPU/GPU for it — bigger models = slower but more accurate.
    model = WhisperModel("base", device="cpu", compute_type="int8")

    segments, _ = model.transcribe(str(video_path), vad_filter=True)

    result = []
    for seg in segments:
        result.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    return result


# ---------- Step 2: Cut, crop to 9:16, burn captions ----------

def make_clip(video_path: Path, start: float, end: float, segments, out_path: Path):
    """
    Cuts [start, end] from the source video, center-crops/scales it to a
    1080x1920 vertical frame, and burns in captions from the transcript
    segments that fall inside this window.
    """
    duration = end - start

    # Build a simple .srt subtitle file for just this clip's time range
    srt_path = out_path.with_suffix(".srt")
    write_srt(segments, start, end, srt_path)

    # Vertical crop: scale up so the shorter side fills 1080, then crop to
    # 1080x1920 from the center. Adjust the crop math if your source isn't
    # 16:9 landscape.
    vf = (
        "scale=1080:-2,crop=1080:1920,"
        f"subtitles={srt_path.as_posix()}:force_style="
        "'FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=3,Outline=2,Alignment=2,MarginV=80'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", str(video_path), "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def write_srt(segments, clip_start, clip_end, srt_path: Path):
    lines = []
    idx = 1
    for s in segments:
        if s["end"] < clip_start or s["start"] > clip_end:
            continue
        rel_start = max(s["start"] - clip_start, 0)
        rel_end = min(s["end"] - clip_start, clip_end - clip_start)
        lines.append(str(idx))
        lines.append(f"{srt_time(rel_start)} --> {srt_time(rel_end)}")
        lines.append(s["text"])
        lines.append("")
        idx += 1
    srt_path.write_text("\n".join(lines), encoding="utf-8")


def srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

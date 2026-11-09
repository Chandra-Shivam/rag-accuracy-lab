"""DEMO: builds the walkthrough video end to end: pages, voice, recording, then one MP4.

Usage: python -m demo.build               (full walkthrough -> demo/out/demo-<date>-<time>.mp4)
       python -m demo.build --short       (2-minute cut -> demo/out/demo-short-<date>-<time>.mp4)
       python -m demo.build --only s08    (one scene -> demo/out/scenes/s08.mp4, for checking)
       python -m demo.build --resume      (same as the first, but keeps scenes already recorded)
       python -m demo.build --resume --no-code --small    (without code scenes, plus a copy under 10 MB for GitHub)
Needs ffmpeg, Playwright with Chromium (pip install -r demo/requirements.txt; python -m playwright install chromium),
and GOOGLE_API_KEY and PINECONE_API_KEY in .env. Live scenes make one Gemini call each; voice clips are cached.
"""
import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

from demo import pages, voice
from demo.record import HOLD, VOICE_DELAY, record_scene
from demo.scenes import SCENES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "demo" / "out"
PORT = 8010  # not 8000, so a server you already have running doesn't clash
APP_URL = f"http://127.0.0.1:{PORT}/"


def start_app():
    """Starts the API in the background. APP_ENV=demo tags its traces, so they can be filtered out of real traffic."""
    env = {**os.environ, "APP_ENV": "demo"}
    OUT.mkdir(parents=True, exist_ok=True)
    log = (OUT / "app.log").open("w")  # kept, so a failed live scene can be explained
    app = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:api", "--port", str(PORT)], cwd=ROOT, env=env,
                           stdout=log, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(APP_URL, timeout=2)
            break
        except OSError:
            time.sleep(1)
    else:
        app.terminate()
        raise RuntimeError("the API did not start")
    warm_up()
    return app


def warm_up():
    """Loads the models and indexes before recording, so the first live scene has no cold-start pause.

    Asks one full question (one Gemini call). Cutting a stream off halfway left the server's generator running.
    """
    request = urllib.request.Request(f"{APP_URL}ask", data=b'{"question": "When is Form 941 due?"}',
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        response.read()


def mux(video, trim, length, audio, out):
    """Joins one scene's video and voice into an MP4 of the same format as every other scene, so they can be joined."""
    total = max(length, VOICE_DELAY + voice.duration(audio) + HOLD)
    delay = round(VOICE_DELAY * 1000)
    graph = (f"[0:v]fps=30,scale=1280:720,tpad=stop_mode=clone:stop_duration={total:.2f}[v];"
             f"[1:a]adelay={delay}:all=1,aresample=48000,apad[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{trim:.2f}", "-i", str(video), "-i", str(audio),
                    "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-ac", "2", str(out)], check=True)
    return total


def duration(path):
    """Length of a media file in seconds, read by ffprobe."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def join(parts, out):
    """Joins the scenes. The picture is copied; the audio is encoded once for the whole video, because copying
    16 AAC pieces adds a few milliseconds of padding per scene and the voice drifted 0.3 s behind by the end."""
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    listing.unlink()


def shrink(src, out, limit_mb=9.3):
    """Re-encodes to fit GitHub's 10 MB limit for videos that play on the page.

    The bitrate is worked out from the length, and two passes make the size land on target.
    15 frames a second is enough for slides and gives each frame more detail, so text stays sharp.
    """
    audio_kbps = 64
    video_kbps = int(limit_mb * 8000 / duration(src) - audio_kbps)
    common = ["-vf", "fps=15", "-c:v", "libx264", "-preset", "slow", "-b:v", f"{video_kbps}k", "-pix_fmt", "yuv420p",
              "-passlogfile", str(OUT / "x264-pass")]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), *common, "-pass", "1", "-an", "-f", "mp4",
                    os.devnull], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), *common, "-pass", "2",
                    "-c:a", "aac", "-b:a", f"{audio_kbps}k", "-ac", "1", str(out)], check=True)
    for log in OUT.glob("x264-pass*"):
        log.unlink()


def main():
    parser = argparse.ArgumentParser(description="Build the demo video.")
    parser.add_argument("--short", action="store_true", help="only the scenes marked short")
    parser.add_argument("--only", help="one scene id, e.g. s08")
    parser.add_argument("--resume", action="store_true", help="reuse scenes already in demo/out/scenes")
    parser.add_argument("--no-code", action="store_true", help="leave out the code scenes (the code is in the repo)")
    parser.add_argument("--small", action="store_true", help="also write a copy under GitHub's 10 MB limit")
    args = parser.parse_args()
    scenes = [s for s in SCENES if (not args.short or s.short) and (not args.only or s.id == args.only)
              and (not args.no_code or s.kind != "code")]
    if not scenes:
        sys.exit(f"no scene with id {args.only!r}")

    print("pages", flush=True)
    page_paths = pages.render(scenes, OUT / "pages")
    print("voice", flush=True)
    audio = {}
    for scene in scenes:
        audio[scene.id] = voice.speak(scene.narration, OUT / "audio")
        print(f"  {scene.id}  {voice.duration(audio[scene.id]):5.1f} s", flush=True)

    parts = [OUT / "scenes" / f"{scene.id}.mp4" for scene in scenes]
    todo = [s for s, part in zip(scenes, parts) if not (args.resume and part.exists())]
    app = start_app() if any(s.kind == "live" for s in todo) else None
    try:
        with sync_playwright() as p:
            # channel="chromium" is Chrome's full headless mode, which has the PDF viewer the citation link needs.
            browser = p.chromium.launch(channel="chromium")
            for scene in todo:
                print(f"record {scene.id} ({scene.kind})", flush=True)
                seconds = voice.duration(audio[scene.id])
                try:
                    video, trim, length = record_scene(browser, scene, seconds, OUT / "video", page_paths.get(scene.id), APP_URL)
                except TimeoutError:
                    if scene.kind != "live":
                        raise
                    # Gemini sometimes stalls for minutes; one fresh try usually works. See demo/out/app.log if not.
                    print(f"  {scene.id}: answer timed out, recording it again", flush=True)
                    video, trim, length = record_scene(browser, scene, seconds, OUT / "video", page_paths.get(scene.id), APP_URL)
                part = OUT / "scenes" / f"{scene.id}.mp4"
                part.parent.mkdir(parents=True, exist_ok=True)
                mux(video, trim, length, audio[scene.id], part)
            browser.close()
    finally:
        if app:
            app.terminate()
            app.wait()
    total = sum(duration(part) for part in parts)

    if args.only:
        print(f"done: {parts[0]}  ({total:.0f} s)")
        return
    # A new name per build: a player that cached an older file under the same name can mix old audio into it.
    name = "demo-short" if args.short else "demo-overview" if args.no_code else "demo"
    out = OUT / f"{name}-{time.strftime('%Y%m%d-%H%M')}.mp4"
    join(parts, out)
    print(f"done: {out}  ({total / 60:.1f} min, {out.stat().st_size / 1e6:.1f} MB)")
    if args.small:
        small = out.with_name(f"{out.stem}-small.mp4")
        shrink(out, small)
        print(f"done: {small}  ({small.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

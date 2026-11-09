"""DEMO: records each scene as a browser video with Playwright, paced to its narration.

Rendered scenes play their page animation; live scenes drive the real chat page at APP_URL.
Captions are added inside the page, timed sentence by sentence against the narration.
"""
import re
import time
from pathlib import Path

from demo.pages import CAPTION_JS

SIZE = {"width": 1280, "height": 720}
VOICE_DELAY = 0.3  # seconds of picture before the voice starts (build.py delays the audio by the same amount)
HOLD = 1.0  # seconds of picture kept after the voice ends
# Larger text on the real app, so it reads at 720p. Changes only how the page looks, not what it does.
APP_CSS = """body { font: 22px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; margin: 56px 72px; }
input { font-size: 22px; padding: 10px 12px; width: 76%; } button { font-size: 22px; padding: 10px 22px; }
#answer { margin-top: 28px; line-height: 1.45; max-width: 1080px; } #sources { margin-top: 18px; } a { font-size: 22px; }"""


def caption_items(narration, seconds):
    """[sentence, start ms, end ms] for each sentence, timed by its share of the characters."""
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", narration.strip()) if s]
    total = sum(len(s) for s in sentences)
    items, start = [], VOICE_DELAY * 1000
    for sentence in sentences:
        end = start + seconds * 1000 * len(sentence) / total
        items.append([sentence, round(start), round(end)])
        start = end
    return items


def _start_captions(page, items, started_at):
    # Wrapped in a function body: evaluate() calls any function an expression returns, and
    # "window.startCaptions = function ..." returns one, which would run it with no arguments.
    script = f"""([items, startedAt]) => {{
      if (typeof window.startCaptions !== 'function') {{ {CAPTION_JS} }}
      window.startCaptions(items, startedAt);
    }}"""
    try:
        page.evaluate(script, [items, started_at])
    except Exception as e:
        print(f"  captions skipped on {page.url[:60]}: {type(e).__name__}", flush=True)


def _wait_for_answer(page, timeout=90):
    """Waits until the streamed answer stops changing for 2 seconds."""
    deadline = time.monotonic() + timeout
    last, stable_since = None, time.monotonic()
    while time.monotonic() < deadline:
        text = page.locator("#answer").text_content() or ""
        if text != last:
            last, stable_since = text, time.monotonic()
        elif text and time.monotonic() - stable_since > 2:
            return
        page.wait_for_timeout(250)
    raise TimeoutError("the answer did not finish streaming")


def _play_live(page, scene, app_url, items, started_at):
    page.add_style_tag(content=APP_CSS)
    page.wait_for_timeout(800)
    page.locator("#question").press_sequentially(scene.show["question"], delay=30)
    page.wait_for_timeout(500)
    page.locator("#ask").click()
    _wait_for_answer(page)
    page.wait_for_timeout(1500)
    links = page.locator("#sources a")
    if scene.show.get("open_citation") and links.count():
        # Same tab, so the PDF lands in this scene's video (a new tab would be recorded as a separate file).
        links.first.evaluate("a => a.removeAttribute('target')")
        links.first.hover()
        page.wait_for_timeout(600)
        links.first.click()
        page.wait_for_timeout(3500)
        _start_captions(page, items, started_at)


def record_scene(browser, scene, seconds, out_dir, page_path=None, app_url=None):
    """Records one scene and returns (webm path, seconds to cut from the start, seconds of usable video)."""
    planned = VOICE_DELAY + seconds + HOLD
    context = browser.new_context(viewport=SIZE, record_video_dir=str(out_dir), record_video_size=SIZE)
    page = context.new_page()
    video_start = time.monotonic()
    page.goto(app_url if scene.kind == "live" else page_path.resolve().as_uri())
    page.wait_for_load_state("load")
    ready = time.monotonic()
    started_at = page.evaluate("Date.now()")
    items = caption_items(scene.narration, seconds)
    _start_captions(page, items, started_at)
    if scene.kind == "live":
        _play_live(page, scene, app_url, items, started_at)
    else:
        page.evaluate(f"window.play({round(planned * 1000)})")
    remaining = planned - (time.monotonic() - ready)
    if remaining > 0:
        page.wait_for_timeout(remaining * 1000)
    length = time.monotonic() - ready
    video = page.video
    context.close()  # the video file is complete only after the context closes
    path = Path(out_dir) / f"{scene.id}.webm"
    video.save_as(str(path))
    video.delete()
    return path, ready - video_start, length

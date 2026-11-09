"""DEMO: renders each non-live scene as a 1280x720 HTML page that the recorder plays.

Every page defines window.play(ms), which runs the scene's animation over the narration's length.
Data shown (code, results, terminal output, trace, CI runs) is read or run at build time, never typed in by hand.
"""
import ast
import html
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JavascriptLexer, PythonLexer

ROOT = Path(__file__).resolve().parent.parent
FORMATTER = HtmlFormatter(style="github-dark", nowrap=True)

CSS = """
:root { --bg: #0e1117; --panel: #161b22; --line: #30363d; --text: #e6edf3; --muted: #8b949e;
        --accent: #58a6ff; --good: #3fb950; --bad: #f85149; --warn: #d29922; }
* { box-sizing: border-box; }
html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: var(--bg); color: var(--text);
             font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
.frame { position: absolute; inset: 0; padding: 40px 64px 130px; }
.label { color: var(--accent); font-size: 16px; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 10px; }
h1 { font-size: 40px; margin: 0 0 22px; line-height: 1.15; }
.subtitle { font-size: 26px; color: var(--muted); margin: 0 0 30px; line-height: 1.35; }
ul.bullets { list-style: none; padding: 0; margin: 0; }
ul.bullets li { font-size: 26px; margin: 0 0 18px; padding-left: 30px; position: relative; line-height: 1.35; }
ul.bullets li::before { content: ""; position: absolute; left: 0; top: 12px; width: 12px; height: 12px;
                        border-radius: 3px; background: var(--accent); }
.fade { opacity: 0; transform: translateY(10px); transition: opacity .6s, transform .6s; }
.fade.on { opacity: 1; transform: none; }
.flow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 26px 34px; margin-top: 10px; }
.step { background: var(--panel); border: 2px solid var(--line); border-radius: 12px; padding: 18px; min-height: 120px;
        transition: border-color .5s, box-shadow .5s; position: relative; }
.step.on { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(88,166,255,.15); }
.step b { display: block; font-size: 22px; margin-bottom: 8px; }
.step span { color: var(--muted); font-size: 17px; line-height: 1.35; }
.step .n { position: absolute; top: 10px; right: 14px; color: var(--muted); font-size: 15px; }
.code-scroll { height: 476px; overflow: hidden; }
.block { margin-bottom: 26px; }
.block .path { color: var(--muted); font: 15px ui-monospace, Menlo, monospace; margin-bottom: 6px; }
.block .path b { color: var(--accent); font-weight: 600; }
pre { margin: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 18px;
      font: 15px/1.45 ui-monospace, Menlo, monospace; white-space: pre; overflow: hidden; }
.term { background: #010409; border: 1px solid var(--line); border-radius: 10px; height: 476px; overflow: hidden;
        padding: 18px 22px; font: 16px/1.45 ui-monospace, Menlo, monospace; white-space: pre; }
.term .cmd { color: var(--good); } .term .exit0 { color: var(--good); } .term .exit1 { color: var(--bad); }
table { border-collapse: collapse; width: 100%; font-size: 19px; }
th, td { text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--line); }
th { color: var(--muted); font-weight: 600; font-size: 16px; }
tr.good td { color: var(--good); } tr.final td { color: var(--accent); font-weight: 600; }
tr.dropped td { color: var(--muted); text-decoration: line-through; }
.cols { display: grid; grid-template-columns: 1.25fr 1fr; gap: 36px; }
.q { font-size: 19px; color: var(--muted); margin-bottom: 18px; }
.node { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; }
.node.child { margin-left: 40px; }
.node b { font-size: 20px; } .node .t { float: right; color: var(--muted); font-size: 17px; }
.node .k { color: var(--muted); font-size: 15px; margin-top: 4px; }
.kv { font: 16px/1.9 ui-monospace, Menlo, monospace; }
.kv .key { color: var(--muted); display: inline-block; width: 140px; }
.pass { color: var(--good); font-weight: 700; } .fail { color: var(--bad); font-weight: 700; }
"""

# Shared with the live scenes, so captions look the same on the real app. Inline styles work on any page.
CAPTION_JS = """
window.startCaptions = function (items, startedAt) {
  let bar = document.getElementById('demo-caption');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'demo-caption';
    bar.style.cssText = 'position:fixed;left:0;right:0;bottom:0;min-height:96px;padding:18px 90px;' +
      'background:rgba(0,0,0,.8);color:#fff;font:24px/1.35 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;' +
      'text-align:center;z-index:2147483647;display:flex;align-items:center;justify-content:center;';
    document.body.appendChild(bar);
  }
  const tick = () => {
    const t = Date.now() - startedAt;
    const item = items.find(i => t >= i[1] && t < i[2]);
    bar.textContent = item ? item[0] : '';
  };
  tick();
  setInterval(tick, 100);
};
"""

# Reveals elements one by one over a share of the scene.
REVEAL_JS = """
const items = document.querySelectorAll('.fade');
items.forEach((el, i) => setTimeout(() => el.classList.add('on'), 500 + i * (ms * SHARE / Math.max(items.length, 1))));
"""


def page(title, body, play_js, label="RAG Accuracy Lab"):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="frame"><div class="label">{html.escape(label)}</div><h1>{html.escape(title)}</h1>{body}</div>
<script>{CAPTION_JS}
window.play = function (ms) {{ {play_js} }};</script></body></html>"""


def slide(show):
    subtitle = f'<p class="subtitle">{html.escape(show["subtitle"])}</p>' if "subtitle" in show else ""
    bullets = "".join(f'<li class="fade">{html.escape(b)}</li>' for b in show.get("bullets", []))
    return page(show["title"], f'{subtitle}<ul class="bullets">{bullets}</ul>', REVEAL_JS.replace("SHARE", "0.6"),
                label=show.get("label", "RAG Accuracy Lab"))


def flow(show):
    steps = "".join(f'<div class="step"><div class="n">{i}</div><b>{html.escape(name)}</b><span>{html.escape(detail)}</span></div>'
                    for i, (name, detail) in enumerate(show["steps"], 1))
    play = """
const steps = document.querySelectorAll('.step');
steps.forEach((el, i) => setTimeout(() => el.classList.add('on'), 400 + i * (ms * 0.85 / steps.length)));
"""
    return page(show["title"], f'<div class="flow">{steps}</div>', play)


def extract(path, target):
    """Source of one top-level function, class or assignment; or, for a (start, end) pair, the lines between two markers."""
    text = (ROOT / path).read_text()
    lines = text.splitlines()
    if isinstance(target, tuple):
        start = next(i for i, line in enumerate(lines) if target[0] in line)
        end = next(i for i in range(start, len(lines)) if target[1] in lines[i])
        return textwrap.dedent("\n".join(lines[start:end + 1])), JavascriptLexer()
    for node in ast.parse(text).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            continue
        if name == target:
            first = node.decorator_list[0].lineno if getattr(node, "decorator_list", None) else node.lineno
            return "\n".join(lines[first - 1:node.end_lineno]), PythonLexer()
    raise ValueError(f"{target} not found in {path}")


def code(show):
    blocks = []
    for path, target in show["blocks"]:
        source, lexer = extract(path, target)
        name = target if isinstance(target, str) else "stream reader"
        blocks.append(f'<div class="block"><div class="path">{html.escape(path)} · <b>{html.escape(name)}</b></div>'
                      f'<pre>{highlight(source, lexer, FORMATTER)}</pre></div>')
    play = """
const box = document.querySelector('.code-scroll');
const distance = box.scrollHeight - box.clientHeight;
if (distance > 0) {
  const begin = performance.now() + 1500, length = Math.max(ms - 3500, 1000);
  const step = now => {
    const p = Math.min(Math.max((now - begin) / length, 0), 1);
    box.scrollTop = distance * p;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
"""
    style = f"<style>{FORMATTER.get_style_defs('pre')}</style>"
    return page(show["title"], f'{style}<div class="code-scroll">{"".join(blocks)}</div>', play)


def run_command(cmd):
    """Runs a command from the repo root and returns (stdout lines, exit code). python means this venv's Python."""
    argv = [sys.executable if cmd[0] == "python" else cmd[0], *cmd[1:]]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300)
    return result.stdout.rstrip().splitlines(), result.returncode


def terminal(show):
    runs = [(" ".join(cmd), *run_command(cmd)) for cmd in show["commands"]]
    data = json.dumps([{"cmd": c, "out": out, "code": rc} for c, out, rc in runs])
    play = f"""
const runs = {data};
const term = document.querySelector('.term');
const budget = ms / runs.length;
const add = (text, cls) => {{
  const line = document.createElement('div');
  if (cls) line.className = cls;
  line.textContent = text;
  term.appendChild(line);
  term.scrollTop = term.scrollHeight;
  return line;
}};
let end = 0;  // each command starts after the previous one has printed its exit code
runs.forEach((run, r) => {{
  const start = Math.max(300 + r * budget, end + 700);
  const typing = run.cmd.length * 35;
  setTimeout(() => {{
    const line = add('$ ', 'cmd');
    [...run.cmd].forEach((ch, i) => setTimeout(() => line.textContent += ch, i * 35));
  }}, start);
  const every = Math.min(150, (budget * 0.6) / Math.max(run.out.length, 1));
  run.out.forEach((text, i) => setTimeout(() => add(text), start + typing + 400 + i * every));
  end = start + typing + 600 + run.out.length * every;
  setTimeout(() => add('exit code ' + run.code, run.code === 0 ? 'exit0' : 'exit1'), end);
}});
"""
    return page(show["title"], '<div class="term"></div>', play)


def results(show):
    """The Final results table from EXPERIMENTS.md, so the video always matches the experiment log."""
    lines = (ROOT / "EXPERIMENTS.md").read_text().split("## Final results", 1)[1].split("\n## ", 1)[0].splitlines()
    table = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines if line.startswith("|")]
    header, rows = table[0], table[2:]
    keep = ["Version", "Change", "Hit@5", "Evidence", "Correct", "Faithful", "Abstain", "Latency (s)"]
    columns = [header.index(name) for name in keep]
    body = "<tr>" + "".join(f"<th>{html.escape(header[c])}</th>" for c in columns) + "</tr>"
    for row in rows:
        version = row[0]
        cls = "final" if "final" in version else "dropped" if "not kept" in row[1] else "good" if version == "v3" else ""
        body += f'<tr class="fade {cls}">' + "".join(f"<td>{html.escape(row[c])}</td>" for c in columns) + "</tr>"
    return page(show["title"], f"<table>{body}</table>", REVEAL_JS.replace("SHARE", "0.55"))


def latest_trace():
    """Newest stream_answer trace in the API project, preferring one from the container (it carries a real commit)."""
    from dotenv import load_dotenv
    from langsmith import Client
    load_dotenv()
    client = Client()
    roots = list(client.list_runs(project_name="irs-rag-api", is_root=True, filter='eq(name, "stream_answer")', limit=20))
    root = next((r for r in roots if (r.extra or {}).get("metadata", {}).get("env") == "docker"), roots[0])
    children = sorted((r for r in client.list_runs(project_name="irs-rag-api", trace_id=root.trace_id) if r.id != root.id),
                      key=lambda r: r.start_time)
    return root, children


def trace(show):
    try:
        root, children = latest_trace()
    except Exception as e:  # no network or no traces: say so on screen rather than fail the whole build
        return page(show["title"], f'<p class="subtitle">Trace unavailable: {html.escape(type(e).__name__)}</p>', "")
    seconds = lambda r: f"{(r.end_time - r.start_time).total_seconds():.2f} s"
    nodes = f'<div class="node fade"><b>{html.escape(root.name)}</b><span class="t">{seconds(root)}</span>' \
            f'<div class="k">root · question in, answer + sources + citations out</div></div>'
    for child in children:
        tokens = f" · {child.total_tokens:,} tokens" if child.total_tokens else ""
        nodes += f'<div class="node child fade"><b>{html.escape(child.name)}</b><span class="t">{seconds(child)}</span>' \
                 f'<div class="k">{html.escape(child.run_type)}{tokens}</div></div>'
    metadata = (root.extra or {}).get("metadata", {})
    keys = ["env", "commit", "model", "prompt", "retrieval", "refused", "citations_ok"]
    kv = "".join(f'<div class="fade"><span class="key">{k}</span>{html.escape(str(metadata.get(k)))}</div>' for k in keys)
    question = html.escape(root.inputs.get("question", ""))
    body = f'<div class="q">Q: {question}</div><div class="cols"><div>{nodes}</div><div class="kv">{kv}</div></div>'
    return page(show["title"], body, REVEAL_JS.replace("SHARE", "0.7"))


def _shorten(text, limit):
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def ci(show):
    try:
        out = subprocess.run(["gh", "run", "list", "--limit", "6", "--json", "conclusion,headBranch,displayTitle,createdAt"],
                             cwd=ROOT, capture_output=True, text=True, timeout=60, check=True).stdout
        runs = json.loads(out)
    except Exception as e:
        return page(show["title"], f'<p class="subtitle">CI runs unavailable: {html.escape(type(e).__name__)}</p>', "")
    rows = "<tr><th></th><th>Branch</th><th>Commit</th><th>When (UTC)</th></tr>"
    for run in runs:
        ok = run["conclusion"] == "success"
        mark = '<span class="pass">✓ passed</span>' if ok else '<span class="fail">✗ failed</span>'
        rows += f'<tr class="fade"><td>{mark}</td><td>{html.escape(run["headBranch"])}</td>' \
                f'<td>{html.escape(_shorten(run["displayTitle"], 52))}</td><td>{run["createdAt"][:16].replace("T", " ")}</td></tr>'
    return page(show["title"], f"<table>{rows}</table>", REVEAL_JS.replace("SHARE", "0.5"))


RENDERERS = {"slide": slide, "flow": flow, "code": code, "terminal": terminal, "results": results, "trace": trace, "ci": ci}


def render(scenes, out_dir):
    """Writes one HTML page per non-live scene. Returns {scene id: path}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for scene in scenes:
        if scene.kind == "live":
            continue
        path = out_dir / f"{scene.id}.html"
        path.write_text(RENDERERS[scene.kind](scene.show))
        paths[scene.id] = path
    return paths


if __name__ == "__main__":
    # Preview: python -m demo.pages renders every page into demo/out/pages, to open in a browser.
    from demo.scenes import SCENES
    os.chdir(ROOT)
    for scene_id, path in render(SCENES, ROOT / "demo" / "out" / "pages").items():
        print(scene_id, path)

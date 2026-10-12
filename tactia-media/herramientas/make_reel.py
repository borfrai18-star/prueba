"""Generate a HyperFrames vertical Reel project in the Tactia style from a JSON spec.

Usage: python3 make_reel.py spec.json out_dir
Spec: {"footer": "...", "scenes": [ {type, dur, ...}, ... ]}
Scene types:
  text: {"l1": "...", "l2": "...(blue)", "sub": optional, "size": optional}
  list: {"n": "1", "q": "...", "sub": optional}
  checks: {"title": "...", "items": [..]}
  end: {"l1": "...", "l2": "...(blue)", "cta": "...", "handle": "@tactia.es"}
"""
import json, sys, pathlib, shutil, html as H

BASE = pathlib.Path(__file__).parent
BLUE, NAVY, BG, CHEV = "#1463FF", "#0E1530", "#F7F9FC", "#E9F1FE"


def words(line, cls=""):
    out = []
    for w in line.split(" "):
        out.append(f'<span class="w {cls}">{H.escape(w)}</span>')
    return " ".join(out)


def scene_html(i, s, start):
    d = s["dur"]
    t = s["type"]
    inner = ""
    if t == "text":
        size = s.get("size", 112)
        inner = (f'<h1 class="hl" style="font-size:{size}px"><span class="ln">{words(s["l1"])}</span>'
                 f'<span class="ln blue">{words(s["l2"])}</span></h1>')
        inner += '<div class="bar"></div>'
        if s.get("sub"):
            inner += f'<p class="sub">{H.escape(s["sub"])}</p>'
    elif t == "list":
        inner = (f'<div class="num">{H.escape(s["n"])}</div>'
                 f'<h2 class="q" style="font-size:{s.get("size", 92)}px">{words(s["q"])}</h2><div class="bar"></div>')
        if s.get("sub"):
            inner += f'<p class="sub">{H.escape(s["sub"])}</p>'
    elif t == "checks":
        items = "".join(f'<div class="ck"><span class="tick">✓</span><span>{H.escape(x)}</span></div>' for x in s["items"])
        inner = f'<h2 class="q" style="font-size:{s.get("size", 96)}px">{words(s["title"])}</h2><div class="bar"></div><div class="cks">{items}</div>'
    elif t == "end":
        inner = (f'<h1 class="hl" style="font-size:{s.get("size", 120)}px"><span class="ln">{words(s["l1"])}</span>'
                 f'<span class="ln blue">{words(s["l2"])}</span></h1><div class="bar"></div>'
                 f'<div class="cta">{H.escape(s["cta"])}</div>'
                 f'<div class="handle">{H.escape(s.get("handle", "@tactia.es"))}</div>')
    return (f'<section id="s{i}" class="clip scene" data-start="{start:.2f}" data-duration="{d:.2f}" '
            f'data-track-index="1">{inner}</section>')


def timeline_js(scenes, total):
    js = []
    js.append(f'tl.fromTo("#prog", {{scaleX: 0}}, {{scaleX: 1, duration: {total:.2f}, ease: "none"}}, 0);')
    js.append(f'tl.fromTo(".chev-wrap", {{y: 0}}, {{y: -70, duration: {total:.2f}, ease: "none"}}, 0);')
    js.append('tl.fromTo("#brand", {opacity: 0, y: -16}, {opacity: 1, y: 0, duration: 0.4, ease: "power2.out"}, 0);')
    t = 0.0
    for i, s in enumerate(scenes):
        sid = f"#s{i}"
        d = s["dur"]
        js.append(f'tl.fromTo("{sid}", {{x: 90, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.32, ease: "power3.out"}}, {t + 0.0:.2f});')
        js.append(f'tl.fromTo("{sid} .num", {{scale: 0.6, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2)"}}, {t + 0.02:.2f});')
        js.append(f'tl.fromTo("{sid} .w", {{y: 70, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.42, ease: "power3.out", stagger: 0.055}}, {t + 0.06:.2f});')
        js.append(f'tl.fromTo("{sid} .bar", {{scaleX: 0}}, {{scaleX: 1, duration: 0.4, ease: "power2.out"}}, {t + 0.45:.2f});')
        js.append(f'tl.fromTo("{sid} .sub", {{y: 24, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.4, ease: "power2.out"}}, {t + 0.6:.2f});')
        js.append(f'tl.fromTo("{sid} .ck", {{x: 40, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.35, ease: "power2.out", stagger: 0.28}}, {t + 0.6:.2f});')
        js.append(f'tl.fromTo("{sid} .cta", {{scale: 0.85, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.45, ease: "back.out(1.8)"}}, {t + 0.7:.2f});')
        js.append(f'tl.fromTo("{sid} .handle", {{opacity: 0}}, {{opacity: 1, duration: 0.4}}, {t + 1.0:.2f});')
        if i < len(scenes) - 1:
            js.append(f'tl.to("{sid}", {{x: -90, opacity: 0, duration: 0.28, ease: "power2.in"}}, {t + d - 0.28:.2f});')
        t += d
    js.append(f'tl.to({{}}, {{duration: 0.01}}, {total - 0.01:.2f});')
    return "\n      ".join(js)


def build(spec, out):
    out = pathlib.Path(out)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(BASE / "node_modules/gsap/dist/gsap.min.js", out / "assets/")
    for w in (400, 500, 800):
        shutil.copy(BASE / f"node_modules/@fontsource/inter-tight/files/inter-tight-latin-{w}-normal.woff2", out / "assets/")
    for f in ("hyperframes.json", "meta.json", "package.json"):
        src = BASE / "reel-test" / f
        if src.exists() and not (out / f).exists():
            shutil.copy(src, out / f)
    scenes = spec["scenes"]
    total = round(sum(s["dur"] for s in scenes), 2)
    t = 0.0
    parts = []
    for i, s in enumerate(scenes):
        parts.append(scene_html(i, s, t))
        t += s["dur"]
    doc = f"""<!doctype html>
<html lang="es" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Inter Tight"; font-weight: 400; src: url("assets/inter-tight-latin-400-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Inter Tight"; font-weight: 500; src: url("assets/inter-tight-latin-500-normal.woff2") format("woff2"); }}
      @font-face {{ font-family: "Inter Tight"; font-weight: 800; src: url("assets/inter-tight-latin-800-normal.woff2") format("woff2"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: {BG}; }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: {BG}; color: {NAVY}; font-family: "Inter Tight", Arial, sans-serif; }}
      .chev {{ position: absolute; border-radius: 90px; transform: rotate(45deg); }}
      #brand {{ position: absolute; left: 90px; top: 236px; font-weight: 500; font-size: 40px; letter-spacing: 0.32em; }}
      #track {{ position: absolute; left: 90px; top: 310px; width: 900px; height: 6px; background: {CHEV}; border-radius: 3px; overflow: hidden; }}
      #prog {{ width: 100%; height: 100%; background: {BLUE}; transform-origin: left center; }}
      .scene {{ position: absolute; left: 90px; top: 520px; width: 880px; height: 960px; }}
      .hl {{ font-weight: 800; line-height: 1.0; letter-spacing: -0.045em; }}
      .ln {{ display: block; }}
      .w {{ display: inline-block; }}
      .blue {{ color: {BLUE}; }}
      .bar {{ width: 90px; height: 8px; background: {BLUE}; margin-top: 56px; transform-origin: left center; }}
      .sub {{ margin-top: 36px; font-weight: 400; font-size: 54px; line-height: 1.22; letter-spacing: -0.01em; }}
      .num {{ font-weight: 800; font-size: 240px; line-height: 0.9; color: {BLUE}; letter-spacing: -0.05em; margin-bottom: 30px; transform-origin: left bottom; }}
      .q {{ font-weight: 800; line-height: 1.04; letter-spacing: -0.04em; }}
      .cks {{ margin-top: 44px; display: flex; flex-direction: column; gap: 26px; }}
      .ck {{ display: flex; gap: 26px; align-items: baseline; font-size: 56px; line-height: 1.15; letter-spacing: -0.01em; }}
      .tick {{ color: {BLUE}; font-weight: 800; width: 44px; flex-shrink: 0; }}
      .cta {{ display: inline-block; margin-top: 52px; padding: 26px 40px; background: {BLUE}; color: #fff; font-weight: 800; font-size: 50px; letter-spacing: -0.02em; border-radius: 22px; transform-origin: left center; }}
      .handle {{ margin-top: 30px; font-weight: 500; font-size: 40px; letter-spacing: 0.04em; }}
      #foot {{ position: absolute; left: 90px; top: 1468px; font-weight: 500; font-size: 26px; letter-spacing: 0.32em; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.2f}" data-width="1080" data-height="1920">
      <div class="clip" data-start="0" data-duration="{total:.2f}" data-track-index="0" style="position:absolute;inset:0">
        <div class="chev-wrap" style="position:absolute;inset:0">
          <div class="chev" style="left:620px;top:900px;width:1000px;height:1000px;background:{CHEV}"></div>
          <div class="chev" style="left:900px;top:900px;width:1000px;height:1000px;background:{BG}"></div>
        </div>
        <div id="brand">TACTIA</div>
        <div id="track"><div id="prog"></div></div>
        <div id="foot">{H.escape(spec.get("footer", "TACTIA / BUILD IN PUBLIC"))}</div>
      </div>
      {"".join(parts)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {timeline_js(scenes, total)}
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""
    (out / "index.html").write_text(doc, encoding="utf-8")
    print(f"built {out} ({total}s)")


if __name__ == "__main__":
    build(json.loads(pathlib.Path(sys.argv[1]).read_text()), sys.argv[2])

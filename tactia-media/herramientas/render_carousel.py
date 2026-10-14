"""Render an Instagram carousel (1080x1350 slides) in the Tactia style.

Usage: python3 render_carousel.py spec.json out_dir
Spec: {"name": "carrusel-x", "footer": "...", "slides": [
  {"type": "cover", "h1": "...", "h2": "...(blue)", "sub": "..."},
  {"type": "item", "n": "1", "title": "...", "body": "..."},
  {"type": "end", "h1": "...", "h2": "...(blue)", "sub": "..."} ]}
"""
import json, sys, pathlib, html as H
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
FONTS = BASE / "node_modules/@fontsource/inter-tight/files"
BLUE, NAVY, BG, CHEV = "#1463FF", "#0E1530", "#F7F9FC", "#E9F1FE"


def ff(w):
    return f"@font-face{{font-family:'Inter Tight';font-weight:{w};src:url('file://{FONTS}/inter-tight-latin-{w}-normal.woff2') format('woff2');}}"


def slide_html(s, idx, total, footer):
    e = H.escape
    if s["type"] in ("cover", "end"):
        mid = (f'<h1 style="margin:0;font-weight:800;font-size:{s.get("size", 112)}px;line-height:0.98;letter-spacing:-0.045em">'
               f'<span style="display:block">{e(s["h1"])}</span><span style="display:block;color:{BLUE}">{e(s["h2"])}</span></h1>'
               f'<div style="width:68px;height:6px;background:{BLUE};margin-top:56px"></div>'
               f'<p style="margin:36px 0 0;font-size:50px;line-height:1.22;letter-spacing:-0.01em">{e(s.get("sub", ""))}</p>')
    else:
        mid = (f'<div style="font-weight:800;font-size:260px;line-height:0.85;color:{BLUE};letter-spacing:-0.05em">{e(s["n"])}</div>'
               f'<h2 style="margin:40px 0 0;font-weight:800;font-size:{s.get("size", 92)}px;line-height:1.02;letter-spacing:-0.04em">{e(s["title"])}</h2>'
               f'<div style="width:68px;height:6px;background:{BLUE};margin-top:48px"></div>'
               f'<p style="margin:36px 0 0;font-size:48px;line-height:1.25;letter-spacing:-0.01em">{e(s["body"])}</p>')
    swipe = "Desliza →" if idx < total - 1 else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff(400)}{ff(500)}{ff(800)}body{{margin:0}}</style></head><body>
<div style="position:relative;width:1080px;height:1350px;box-sizing:border-box;padding:96px 84px 84px;background:{BG};color:{NAVY};font-family:'Inter Tight',Arial,sans-serif;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden">
  <div style="position:absolute;left:640px;top:560px;width:900px;height:900px;border-radius:90px;background:{CHEV};transform:rotate(45deg)"></div>
  <div style="position:absolute;left:890px;top:560px;width:900px;height:900px;border-radius:90px;background:{BG};transform:rotate(45deg)"></div>
  <div style="position:relative;display:flex;justify-content:space-between;align-items:baseline">
    <div style="font-weight:500;font-size:36px;letter-spacing:0.32em">TACTIA</div>
    <div style="font-weight:500;font-size:28px;letter-spacing:0.08em;color:{BLUE}">{idx + 1}/{total}</div>
  </div>
  <div style="position:relative;max-width:900px">{mid}</div>
  <div style="position:relative;display:flex;justify-content:space-between;align-items:baseline">
    <div style="font-weight:500;font-size:20px;letter-spacing:0.32em">{e(footer)}</div>
    <div style="font-weight:800;font-size:32px;color:{BLUE}">{swipe}</div>
  </div>
</div></body></html>"""


def main(spec_path, out_dir):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    slides = spec["slides"]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(slides):
            f = out / f"{spec['name']}-{i + 1}.html"
            f.write_text(slide_html(s, i, len(slides), spec.get("footer", "TACTIA / PARA PYMES")), encoding="utf-8")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(300); pg.evaluate("document.fonts.ready")
            pg.screenshot(path=str(out / f"{spec['name']}-{i + 1}.png"))
            print("ok", f"{spec['name']}-{i + 1}.png")
        b.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

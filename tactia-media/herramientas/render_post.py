"""Render Tactia LinkedIn post images (1080x1080) in the brand style."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
FONTS = BASE / "node_modules/@fontsource/inter-tight/files"

def font_face(w):
    return f"@font-face{{font-family:'Inter Tight';font-weight:{w};src:url('file://{FONTS}/inter-tight-latin-{w}-normal.woff2') format('woff2');}}"

def html(p):
    accent = "#1463FF"
    if p.get("steps"):
        body = "".join(
            f'<div style="display:flex;gap:22px;align-items:baseline;font-size:{p.get("step_size",34)}px;line-height:1.2;letter-spacing:-0.01em">'
            f'<span style="width:28px;flex-shrink:0;font-weight:800;color:{accent}">{i+1}</span><span>{s}</span></div>'
            for i, s in enumerate(p["steps"]))
        lower = f'<div style="display:flex;flex-direction:column;gap:14px">{body}</div>'
    else:
        lower = (f'<p style="margin:0;font-weight:400;font-size:{p.get("sub_size",48)}px;line-height:1.22;letter-spacing:-0.01em">'
                 f'<span style="display:block">{p["sub1"]}</span><span style="display:block;color:{accent}">{p["sub2"]}</span></p>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_face(400)}{font_face(500)}{font_face(800)}
body{{margin:0}}</style></head><body>
<div style="position:relative;width:1080px;height:1080px;box-sizing:border-box;padding:84px 80px 76px;background:#F7F9FC;color:#0E1530;font-family:'Inter Tight',Arial,sans-serif;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden">
  <div style="position:absolute;left:694px;top:276px;width:775px;height:775px;border-radius:80px;background:#E9F1FE;transform:rotate(45deg)"></div>
  <div style="position:absolute;left:909px;top:276px;width:775px;height:775px;border-radius:80px;background:#F7F9FC;transform:rotate(45deg)"></div>
  <div style="position:absolute;left:878px;top:732px;width:202px;height:348px;background:#E9F1FE;clip-path:polygon(0 0,100% 202px,100% 100%,0 100%)"></div>
  <div style="position:relative;font-weight:500;font-size:36px;letter-spacing:0.32em">TACTIA</div>
  <h1 style="position:relative;margin:0;font-weight:800;font-size:{p.get('h_size',108)}px;line-height:0.98;letter-spacing:-0.045em;max-width:920px"><span style="display:block">{p['h1']}</span><span style="display:block;color:{accent}">{p['h2']}</span></h1>
  <div style="position:relative;display:flex;flex-direction:column;gap:30px">
    <div style="width:68px;height:6px;background:{accent}"></div>
    {lower}
  </div>
  <div style="position:relative;font-weight:500;font-size:19px;letter-spacing:0.32em">{p['footer']}</div>
</div></body></html>"""

def main(spec_path, out_dir):
    specs = json.loads(pathlib.Path(spec_path).read_text())
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1080})
        for name, p in specs.items():
            f = out / f"{name}.html"; f.write_text(html(p), encoding="utf-8")
            pg.goto(f"file://{f}"); pg.wait_for_timeout(400)
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=str(out / f"{name}.png"))
            print("ok", name)
        b.close()

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

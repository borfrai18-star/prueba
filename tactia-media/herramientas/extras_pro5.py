"""Extras del montaje v5:
- behind_head(): mete textos grandes ENTRE el fondo y la persona (texto detrás de la cabeza).
- write_ass_editorial(): subtítulos donde la palabra clave (*marcada* en el guion) va grande en cursiva con serifa
  y el resto pequeño en sans; aparecen palabra a palabra.
"""
import html as H, pathlib, re, subprocess
from playwright.sync_api import sync_playwright
from montar_video import W, HGT, FPS, run, NAVY, BLUE

SERIF = pathlib.Path(__file__).parent / "node_modules/@fontsource/instrument-serif/files/instrument-serif-latin-400-italic.woff2"


def behind_html(text, size, y, color):
    e = H.escape
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>"
            f"@font-face{{font-family:'IS';font-style:italic;src:url('file://{SERIF}') format('woff2')}}"
            f"html,body{{margin:0;background:transparent}}</style></head><body>"
            f"<div style='position:relative;width:{W}px;height:{HGT}px;overflow:hidden'>"
            f"<div style=\"position:absolute;left:-40px;right:-40px;top:{y}px;text-align:center;font-family:'IS',serif;"
            f"font-style:italic;font-size:{size}px;line-height:0.86;letter-spacing:-0.035em;color:{color};"
            f"text-shadow:0 10px 50px rgba(0,0,0,.35);white-space:nowrap\">{'<br>'.join(e(x) for x in text.split('|'))}</div>"
            f"</div></body></html>")


def behind_head(norm, mask, items, out, tmp):
    """items: [{"t0","t1","text","size"?,"y"?,"color"?}] en tiempo del clip original."""
    pngs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": HGT})
        for i, it in enumerate(items):
            f = tmp / f"behind{i}.html"
            f.write_text(behind_html(it["text"], it.get("size", 330), it.get("y", 150), it.get("color", "#FFFFFF")), encoding="utf-8")
            pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(150)
            p = tmp / f"behind{i}.png"; pg.screenshot(path=str(p), omit_background=True); pngs.append(p)
        b.close()
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(norm)]).stdout)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(norm), "-i", str(mask)]
    for p in pngs:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.5:.2f}", "-i", str(p)]
    fc = "[0:v]split=2[bg][fgsrc];[1:v]format=gray,scale=%d:%d[m];[fgsrc][m]alphamerge[fg];" % (W, HGT)
    last = "bg"
    for i, it in enumerate(items):
        t0, t1 = float(it["t0"]), float(it["t1"])
        # entra con fundido y un ligero zoom desde 1.08 (sensación de "aterrizar")
        fc += (f"[{i + 2}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.18:alpha=1,fade=t=out:st={max(t0, t1 - 0.2):.2f}:d=0.2:alpha=1[t{i}];"
               f"[{last}][t{i}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.2f},{t1:.2f})'[b{i}];")
        last = f"b{i}"
    fc += f"[{last}][fg]overlay=0:0:format=auto,format=yuv420p[v]"
    run(cmd + ["-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15",
               "-c:a", "copy", "-t", f"{dur:.3f}", str(out)])


def ass_time(t):
    t = max(0.0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def write_ass_editorial(lines, path, hide_zones, end_from=1e9, y=1290, clean=False):
    """lines: listas de (t0, t1, palabra, fin_tramo). Palabras con *asteriscos* = clave."""
    clean_style = clean
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {HGT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sm,{'Inter Display Medium' if clean else 'Inter Display'},{56 if clean else 64},&H00FFFFFF,&H00FFFFFF,&H00301E0E,&H96000000,{0 if clean else -1},0,0,0,100,100,0,0,1,0,{2 if clean else 4},5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for i, ln in enumerate(lines):
        t0 = ln[0][0]
        if any(a - 0.05 <= t0 <= b for a, b in hide_zones):
            continue
        t1 = min(lines[i + 1][0][0], ln[-1][1] + 0.5) if i + 1 < len(lines) else ln[-1][1] + 0.4
        yy = 900 if t0 >= end_from - 0.05 else y
        parts = []
        for (a, b, w, *_) in ln:
            # cada palabra aparece cuando se dice (alpha 0 -> visible)
            delay = int(max(0, (a - t0)) * 1000)
            appear = f"{{\\alpha&HFF&\\t({delay},{delay + 80},\\alpha&H00&)}}"
            if w.startswith("*") or w.rstrip(".,:;?!»").endswith("*"):
                clean = w.replace("*", "")
                if clean_style:
                    parts.append(appear + f"\\N{{\\fs150\\b1\\shad3}}{clean}{{\\fs56\\b0\\shad2}}\\N")
                else:
                    parts.append(appear + f"{{\\fnInstrument Serif\\i1\\b0\\fs130\\shad5}}{clean}{{\\fnInter Display\\i0\\b1\\fs64\\shad4}}")
            else:
                parts.append(appear + w)
        txt = f"{{\\an5\\pos({W // 2},{yy})}}" + " ".join(parts)
        ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Sm,,0,0,0,,{txt}")
    pathlib.Path(path).write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")


def editorial_look(norm, mask, items, out, tmp):
    """Fondo un poco más oscuro y desenfocado (la persona destaca), textos detrás de la cabeza,
    etalonaje cálido con contraste suave y grano fino de película."""
    pngs = []
    if items:
        with sync_playwright() as pw:
            b = pw.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": HGT})
            for i, it in enumerate(items):
                f = tmp / f"behind{i}.html"
                f.write_text(behind_html(it["text"], it.get("size", 360), it.get("y", 420), it.get("color", "#FFFFFF")), encoding="utf-8")
                pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(150)
                p = tmp / f"behind{i}.png"; pg.screenshot(path=str(p), omit_background=True); pngs.append(p)
            b.close()
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(norm)]).stdout)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(norm), "-i", str(mask)]
    for p in pngs:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur + 0.5:.2f}", "-i", str(p)]
    fc = ("[0:v]split=2[bgsrc][fgsrc];"
          "[bgsrc]eq=brightness=-0.07:saturation=0.78:contrast=0.96,gblur=sigma=7[bg];"
          f"[1:v]format=gray,scale={W}:{HGT},curves=master='0/0 0.3/0.1 0.7/0.97 1/1',gblur=sigma=1.2[m];"
          "[fgsrc]eq=contrast=1.04:saturation=1.03[fgc];[fgc][m]alphamerge[fg];")
    last = "bg"
    for i, it in enumerate(items):
        t0, t1 = float(it["t0"]), float(it["t1"])
        fc += (f"[{i + 2}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.25:alpha=1,fade=t=out:st={max(t0, t1 - 0.25):.2f}:d=0.25:alpha=1[t{i}];"
               f"[{last}][t{i}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.2f},{t1:.2f})'[b{i}];")
        last = f"b{i}"
    fc += (f"[{last}][fg]overlay=0:0:format=auto,"
           "curves=r='0/0.02 0.5/0.52 1/0.98':g='0/0.01 0.5/0.5 1/0.97':b='0/0.04 0.5/0.48 1/0.93',"
           "noise=alls=5:allf=t,vignette=a=PI/6,format=yuv420p[v]")
    run(cmd + ["-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15",
               "-c:a", "copy", "-t", f"{dur:.3f}", str(out)])

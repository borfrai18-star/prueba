#!/usr/bin/env python3
"""Montaje "pro" de un vídeo a cámara: cortes en las pausas con transiciones variadas (corte seco con
punch-in, barrido lateral, zoom, flash, desenfoque), subtítulos palabra a palabra con la palabra activa
en azul Tactia, gráficos animados en momentos clave, whoosh en las transiciones, etalonaje suave y
tarjeta final. NUNCA invierte la imagen.

spec.json:
{"name": "V02", "clip": "/ruta/IMG.MOV", "out_dir": "entregas",
 "chunks": [[0.73, 3.32, "texto dicho en ese tramo"], ...],      # tramos con voz (tiempo del clip original)
 "graphics": [{"t0": 3.7, "t1": 7.7, "kind": "badge", "text": "4 PALABRAS"},
              {"t0": 21.7, "t1": 26.0, "kind": "bubble", "text": "¿Quieres hidratación?"}],
 "end_secs": 3.3, "cut_pause": 0.3, "keep_pause": 0.1, "min_seg": 1.5}
"""
import html as H, json, math, pathlib, re, subprocess, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from montar_video import BASE, FPS, W, HGT, BG, BLUE, NAVY, probe, run, ff, FONTS  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# ---------- 1. cortes ----------

def segments_from_chunks(chunks, cut_pause=0.3, keep=0.1, min_seg=1.5):
    """Trozos (a, b) del clip original. Entre dos tramos de voz: si la pausa es larga se quita,
    si es corta se parte por la mitad (solo cambia el encuadre)."""
    segs = []
    cur = max(0.0, chunks[0][0] - 0.15)
    for i, (a, b, _) in enumerate(chunks):
        if i + 1 < len(chunks):
            na = chunks[i + 1][0]
            gap = na - b
            if gap >= cut_pause:
                segs.append((cur, b + keep)); cur = na - keep
            else:
                m = (b + na) / 2
                segs.append((cur, m)); cur = m
        else:
            segs.append((cur, b + 0.25))
    # une trozos cortos con el siguiente (o con el anterior si es el último)
    out = []
    for a, b in segs:
        if out and (out[-1][1] - out[-1][0]) < min_seg:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    if len(out) > 1 and (out[-1][1] - out[-1][0]) < min_seg:
        _, b = out.pop(); out[-1] = (out[-1][0], b)
    return out


# encuadres alternos: (zoom, dx, dy). Suaves: la cara siempre queda dentro.
FRAMES = [(1.00, 0, 0), (1.16, 40, -30), (1.06, -30, 0), (1.24, 20, -50), (1.00, 0, 0), (1.18, -40, -30), (1.10, 30, -10)]
# transiciones en bucle: (nombre xfade, duración, whoosh)
TRANS = [("cut", 0.034, False), ("slideleft", 0.20, True), ("cut", 0.034, False), ("zoomin", 0.24, True),
         ("cut", 0.034, False), ("hblur", 0.20, True), ("fadewhite", 0.18, False), ("cut", 0.034, False),
         ("slideright", 0.20, True), ("cut", 0.034, False), ("smoothup", 0.22, True)]


def zoom_filter(k):
    z0, dx, dy = FRAMES[k % len(FRAMES)]
    z = f"({z0}+0.0008*on+0.04*max(0\\,1-on/4))"
    x = f"(iw/2-(iw/zoom/2)+{dx * 1.5})"
    y = f"(ih/2-(ih/zoom/2)+{dy * 1.5})"
    return (f"scale={int(W * 1.5)}:{int(HGT * 1.5)}:flags=bicubic,"
            f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{HGT}:fps={FPS},settb=AVTB,format=yuv420p")


# ---------- 2. gráficos (PNG transparentes) ----------

def gfx_html(kind, text):
    e = H.escape
    if kind == "badge":
        inner = (f'<div style="position:absolute;left:0;right:0;top:170px;display:flex;justify-content:center">'
                 f'<div style="background:{BG};color:{NAVY};border-radius:999px;padding:26px 54px;font-weight:800;'
                 f'font-size:66px;letter-spacing:-0.03em;box-shadow:0 14px 40px rgba(14,21,48,.3);'
                 f'border:6px solid {BLUE}">{e(text)}</div></div>')
    elif kind == "bubble":
        inner = (f'<div style="position:absolute;left:90px;right:90px;top:170px;display:flex;justify-content:center">'
                 f'<div style="background:#fff;color:{NAVY};border-radius:36px 36px 36px 8px;padding:30px 44px;'
                 f'font-weight:800;font-size:58px;line-height:1.08;letter-spacing:-0.03em;text-align:center;'
                 f'box-shadow:0 14px 40px rgba(14,21,48,.3)">{e(text)}</div></div>')
    elif kind == "bubble2":
        inner = (f'<div style="position:absolute;left:90px;right:90px;top:360px;display:flex;justify-content:center">'
                 f'<div style="background:{BLUE};color:#fff;border-radius:36px 36px 8px 36px;padding:30px 44px;'
                 f'font-weight:800;font-size:58px;line-height:1.08;letter-spacing:-0.03em;text-align:center;'
                 f'box-shadow:0 14px 40px rgba(14,21,48,.3)">{e(text)}</div></div>')
    elif kind == "stat":
        big, small = text.split("|", 1)
        inner = (f'<div style="position:absolute;left:0;right:0;top:150px;display:flex;justify-content:center">'
                 f'<div style="background:{NAVY};color:#fff;border-radius:34px;padding:26px 60px;text-align:center;'
                 f'box-shadow:0 14px 40px rgba(14,21,48,.35)">'
                 f'<div style="font-weight:800;font-size:120px;line-height:1;letter-spacing:-0.05em;color:#fff">{e(big)}</div>'
                 f'<div style="margin-top:8px;font-weight:800;font-size:46px;letter-spacing:-0.02em;color:#9DBBFF">{e(small)}</div>'
                 f'</div></div>')
    else:  # end
        inner = (f'<div style="position:absolute;left:0;right:0;bottom:0;height:720px;'
                 f'background:linear-gradient(to bottom, rgba(247,249,252,0) 0, {BG} 200px)"></div>'
                 f'<div style="position:absolute;left:84px;right:84px;bottom:300px;color:{NAVY}">'
                 f'<div style="font-weight:500;font-size:38px;letter-spacing:0.32em">TACTIA</div>'
                 f'<div style="margin-top:18px;font-weight:800;font-size:84px;line-height:1;letter-spacing:-0.045em">'
                 f'Tactia prepara.<br><span style="color:{BLUE}">Tú decides.</span></div>'
                 f'<div style="margin-top:22px;font-weight:500;font-size:40px">@tactia.es</div></div>')
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{ff(500)}{ff(800)}"
            f"html,body{{margin:0;background:transparent}}</style></head><body>"
            f"<div style=\"position:relative;width:{W}px;height:{HGT}px;font-family:'Inter Tight',Arial,sans-serif\">{inner}</div>"
            f"</body></html>")


def render_gfx(items, tmp):
    paths = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": HGT})
        for name, kind, text in items:
            f = tmp / f"{name}.html"; f.write_text(gfx_html(kind, text), encoding="utf-8")
            pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(120)
            p = tmp / f"{name}.png"; pg.screenshot(path=str(p), omit_background=True); paths[name] = p
        b.close()
    return paths


# ---------- 3. subtítulos palabra a palabra (ASS) ----------

def word_times(chunks):
    """Reparte las palabras de cada tramo proporcionalmente a su longitud. Devuelve [(t0, t1, palabra)]."""
    out = []
    for a, b, text in chunks:
        words = text.split()
        weights = [len(re.sub(r"[^\wáéíóúñü]", "", w, flags=re.I)) + 1.2 for w in words]
        tot = sum(weights); t = a
        for i, (w, wt) in enumerate(zip(words, weights)):
            d = (b - a) * wt / tot
            out.append((t, t + d, w, i == len(words) - 1)); t += d
    return out


GLUE = {"de","la","el","en","a","que","y","o","con","por","tu","su","lo","los","las","un","una","al","del",
        "es","se","te","le","ya","no","me","mi","si","sí,","más","va","le","ni","para","como","pero","son"}


def caption_lines(words, max_words=4, max_chars=26):
    """Agrupa palabras en líneas cortas: corta en puntuación y al final de cada tramo de voz,
    y no deja colgando aperturas (¿ «) ni palabras de enlace."""
    def is_glue(w):
        t = w.lower().strip("«»\"")
        return t.startswith(("¿", "«")) or t in GLUE
    lines, cur = [], []
    for w in words:
        cand = cur + [w]
        chars = len(" ".join(x[2] for x in cand))
        if cur and (len(cand) > max_words or chars > max_chars):
            moved = []
            while len(cur) > 1 and is_glue(cur[-1][2]) and len(moved) < 2:
                moved.insert(0, cur.pop())
            lines.append(cur); cur = moved + [w]
        else:
            cur = cand
        if (re.search(r"[.?!:,»]$", w[2]) or (len(w) > 3 and w[3])) and len(cur) >= 2 and not is_glue(cur[-1][2]):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    return lines


def ass_time(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


ACTIVE = "#FFD60A"   # palabra que se está diciendo


def write_ass(lines, path, y_default=1250, y_end=None, end_from=None):
    def col(hexrgb):  # "#RRGGBB" -> &H00BBGGRR
        r, g, b = hexrgb[1:3], hexrgb[3:5], hexrgb[5:7]; return f"&H00{b}{g}{r}".upper()
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {HGT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,88,{col(ACTIVE)},&H00FFFFFF,{col(NAVY)},&H80000000,-1,0,0,0,100,100,-1,0,1,9,3,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for i, ln in enumerate(lines):
        t0 = ln[0][0]; t1 = ln[-1][1]
        if i + 1 < len(lines):
            t1 = min(lines[i + 1][0][0], t1 + 0.6)   # se mantiene hasta que entra la siguiente (máx. 0,6 s)
        else:
            t1 = t1 + 0.4
        y = y_default
        if y_end is not None and end_from is not None and t0 >= end_from - 0.01:
            y = y_end
        parts = []
        for (a, b, w, *_) in ln:
            parts.append(f"{{\\k{int(round((b - a) * 100))}}}{w}")
        txt = f"{{\\an5\\pos({W // 2},{y})\\fscx86\\fscy86\\t(0,110,\\fscx100\\fscy100)}}" + " ".join(parts)
        ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,0,,{txt}")
    path.write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")


# ---------- 4. montaje ----------

def main(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    root = pathlib.Path(spec_path).parent
    out_dir = root / spec.get("out_dir", "entregas"); out_dir.mkdir(parents=True, exist_ok=True)
    (BASE / "tmp-montaje").mkdir(exist_ok=True)
    tmp = pathlib.Path(spec["tmp"]) if spec.get("tmp") else pathlib.Path(tempfile.mkdtemp(prefix=f"{spec['name']}-", dir=BASE / "tmp-montaje"))
    tmp.mkdir(parents=True, exist_ok=True); print("tmp:", tmp)
    src = pathlib.Path(spec["clip"])

    # 4a. normalización + etalonaje suave (sin invertir nada)
    info = probe(src)
    vf = []
    if info["trc"] in ("arib-std-b67", "smpte2084"):
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")
    vf += [f"scale={W}:{HGT}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={W}:{HGT}", f"fps={FPS}",
           "eq=contrast=1.06:saturation=1.12:brightness=0.005", "unsharp=5:5:0.35", "vignette=a=PI/7",
           "format=yuv420p", "setsar=1"]
    norm = tmp / "norm.mp4"
    if not norm.exists():
      run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vf", ",".join(vf),
         "-af", "aresample=48000", "-ac", "2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15",
         "-c:a", "aac", "-b:a", "192k", str(norm)])
    dur = probe(norm)["dur"]

    chunks = [(float(a), float(b), t) for a, b, t in spec["chunks"]]
    segs = segments_from_chunks(chunks, spec.get("cut_pause", 0.3), spec.get("keep_pause", 0.1), spec.get("min_seg", 1.5))
    segs = [(a, min(b, dur)) for a, b in segs]
    n = len(segs)
    trans = [TRANS[k % len(TRANS)] for k in range(n - 1)]

    # cada trozo se renderiza a su propio archivo (xfade no se lleva bien con trim+split)
    from concurrent.futures import ThreadPoolExecutor
    def render_seg(k):
        a, b = segs[k]; f = tmp / f"seg{k}.mp4"
        if f.exists():
            return probe(f)["dur"]
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(norm),
             "-vf", zoom_filter(k), "-af", "aresample=48000", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
             "-c:a", "aac", "-b:a", "192k", str(f)])
        return probe(f)["dur"]
    with ThreadPoolExecutor(max_workers=3) as ex:
        seg_dur = list(ex.map(render_seg, range(n)))

    # tiempos de salida de cada trozo
    out_start, t = [], 0.0
    for k in range(n):
        out_start.append(t); t += seg_dur[k]
        if k < n - 1:
            t -= trans[k][1]
    total = t

    def to_out(ti):
        for k, (a, b) in enumerate(segs):
            if a - 1e-6 <= ti <= b + 1e-6:
                return out_start[k] + (ti - a)
        # fuera de los trozos (dentro de una pausa quitada): al borde más cercano
        k = min(range(n), key=lambda i: min(abs(ti - segs[i][0]), abs(ti - segs[i][1])))
        a, b = segs[k]
        return out_start[k] + (min(max(ti, a), b) - a)

    print("trozos:", [(round(a, 2), round(b, 2)) for a, b in segs])
    print("transiciones:", [x[0] for x in trans])
    print(f"duración final {total:.1f}s (original {dur:.1f}s)")

    # 4b. subtítulos
    end_s = float(spec.get("end_secs", 3.3)); end_t0 = max(0.0, total - end_s)
    words = [(to_out(a), to_out(b), w, e) for a, b, w, e in word_times(chunks)]
    lines = caption_lines(words)
    ass = tmp / "caps.ass"
    write_ass(lines, ass, y_default=spec.get("cap_y", 1250), y_end=930, end_from=end_t0)

    # 4c. gráficos
    gitems = [("end", "end", "")] + [(f"g{i}", g["kind"], g["text"]) for i, g in enumerate(spec.get("graphics", []))]
    png = render_gfx(gitems, tmp)
    overlays = []  # (png, t0, t1, anim)
    for i, g in enumerate(spec.get("graphics", [])):
        overlays.append((png[f"g{i}"], to_out(g["t0"]), to_out(g["t1"]), "drop"))
    overlays.append((png["end"], end_t0, total + 1, "fade"))

    # 4d. whoosh sintético
    whoosh = tmp / "whoosh.wav"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "anoisesrc=c=pink:r=48000:d=0.4:a=0.9",
         "-af", "highpass=f=250,lowpass=f=2200,afade=t=in:st=0:d=0.06,afade=t=out:st=0.14:d=0.26,volume=0.55",
         "-ac", "2", str(whoosh)])
    wh_times = [out_start[k + 1] - trans[k][1] / 2 for k in range(n - 1) if trans[k][2]]

    # 4e. filtro
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for k in range(n):
        cmd += ["-i", str(tmp / f"seg{k}.mp4")]
    fc = ""
    for k in range(n):
        fc += f"[{k}:v]settb=AVTB,format=yuv420p[v{k}];[{k}:a]asetpts=PTS-STARTPTS[a{k}];"
    lastv, lasta, off = "v0", "a0", 0.0
    for k in range(n - 1):
        name, d, _ = trans[k]
        off = out_start[k + 1]  # el siguiente trozo empieza aquí (ya descontada la transición)
        tname = "fade" if name == "cut" else name
        fc += f"[{lastv}][v{k + 1}]xfade=transition={tname}:duration={d}:offset={off:.3f}[x{k}];"
        fc += f"[{lasta}][a{k + 1}]acrossfade=d={d}:c1=tri:c2=tri[y{k}];"
        lastv, lasta = f"x{k}", f"y{k}"
    # gráficos con animación de entrada
    idx = n
    for j, (p, t0, t1, anim) in enumerate(overlays):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total + 1:.2f}", "-i", str(p)]
        if anim == "drop":
            fc += (f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.18:alpha=1,"
                   f"fade=t=out:st={max(t0, t1 - 0.22):.2f}:d=0.22:alpha=1[o{j}];")
            yexpr = f"'-110*pow(1-min(1,(t-{t0:.2f})/0.35),2)'"
            fc += (f"[{lastv}][o{j}]overlay=x=0:y={yexpr}:shortest=1:eof_action=pass:"
                   f"enable='between(t,{t0:.2f},{t1:.2f})'[w{j}];")
        else:
            fc += f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.4:alpha=1[o{j}];"
            fc += (f"[{lastv}][o{j}]overlay=0:0:shortest=1:eof_action=pass:"
                   f"enable='between(t,{t0:.2f},{t1:.2f})'[w{j}];")
        lastv = f"w{j}"; idx += 1
    # subtítulos
    fc += f"[{lastv}]ass='{ass}'[vcap];"
    # audio: voz + whooshes
    if wh_times:
        cmd += ["-i", str(whoosh)]
        fc += f"[{idx}:a]asplit={len(wh_times)}" + "".join(f"[s{i}]" for i in range(len(wh_times))) + ";"
        for i, tw in enumerate(wh_times):
            ms = int(max(0.0, tw - 0.12) * 1000)
            fc += f"[s{i}]adelay={ms}|{ms}[d{i}];"
        fc += (f"[{lasta}]" + "".join(f"[d{i}]" for i in range(len(wh_times))) +
               f"amix=inputs={len(wh_times) + 1}:normalize=0:dropout_transition=0[mix];")
        lasta = "mix"
    fc += f"[{lasta}]loudnorm=I=-14:LRA=11:TP=-1.5,aresample=48000[aout]"
    out = out_dir / f"{spec['name']}.mp4"
    cmd += ["-filter_complex", fc, "-map", "[vcap]", "-map", "[aout]", "-t", f"{total:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    (tmp / "cmd.txt").write_text(" ".join(map(str, cmd)))
    run(cmd)
    print("ok", out, f"{probe(out)['dur']:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1])

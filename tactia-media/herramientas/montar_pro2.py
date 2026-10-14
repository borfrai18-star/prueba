#!/usr/bin/env python3
"""Montaje PRO v2 de un vídeo a cámara. Solo se oye la voz (tratada), sin sonidos de transición.

- Cortes en las pausas con transiciones variadas (corte seco con punch-in, barrido, zoom, flash, desenfoque).
- Gráficos ANIMADOS fotograma a fotograma (HTML + Playwright): título del gancho, píldoras, contadores,
  bocadillos con efecto máquina de escribir, listas que aparecen, estrellas, interruptor, tarjeta final.
- Subtítulos palabra a palabra con rebote de entrada y palabra activa en amarillo.
- Etalonaje suave y voz con ecualización + compresión.
- NUNCA invierte la imagen.

spec.json: ver v*pro2.json. Claves: name, clip, out_dir, tmp (opcional, caché), chunks [[a,b,"texto"],...],
graphics [{"t0","t1","kind","zone":"top|low","pos":{...}, ...parámetros}], end_secs.
"""
import html as H, json, math, os, pathlib, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from montar_video import BASE, FPS, W, HGT, BG, BLUE, NAVY, probe, run, ff  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

YELLOW = "#FFD60A"
CAP_Y, CAP_Y_LOW, LOW_Y = 1250, 1580, 1130   # subtítulos normal / con gráfico abajo / centro del gráfico bajo


# ---------- cortes y encuadres ----------

def segments_from_chunks(chunks, cut_pause=0.3, keep=0.1, min_seg=1.5):
    segs, cur = [], max(0.0, chunks[0][0] - 0.15)
    for i, (a, b, _) in enumerate(chunks):
        if i + 1 < len(chunks):
            na = chunks[i + 1][0]; gap = na - b
            if gap >= cut_pause:
                segs.append((cur, b + keep)); cur = na - keep
            else:
                m = (b + na) / 2; segs.append((cur, m)); cur = m
        else:
            segs.append((cur, b + 0.25))
    out = []
    for a, b in segs:
        if out and (out[-1][1] - out[-1][0]) < min_seg:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    if len(out) > 1 and (out[-1][1] - out[-1][0]) < min_seg:
        _, b = out.pop(); out[-1] = (out[-1][0], b)
    return out


FRAMES = [(1.00, 0, 0), (1.18, 40, -30), (1.06, -30, 0), (1.26, 20, -50), (1.00, 0, 0), (1.20, -40, -30), (1.10, 30, -10), (1.30, 0, -40)]
TRANS = [("cut", 0.034), ("slideleft", 0.20), ("cut", 0.034), ("zoomin", 0.24), ("cut", 0.034), ("hblur", 0.20),
         ("fadewhite", 0.16), ("cut", 0.034), ("slideright", 0.20), ("cut", 0.034), ("smoothup", 0.22), ("cut", 0.034),
         ("circleopen", 0.22), ("cut", 0.034), ("slideup", 0.20)]


def zoom_filter(k):
    z0, dx, dy = FRAMES[k % len(FRAMES)]
    z = f"({z0}+0.0008*on+0.05*max(0\\,1-on/4))"
    return (f"scale={int(W * 1.5)}:{int(HGT * 1.5)}:flags=bicubic,"
            f"zoompan=z='{z}':x='(iw/2-(iw/zoom/2)+{dx * 1.5})':y='(ih/2-(ih/zoom/2)+{dy * 1.5})':d=1:s={W}x{HGT}:fps={FPS},"
            f"settb=AVTB,format=yuv420p")


# ---------- gráficos animados ----------

JS = r"""
const EB=x=>{const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
const EC=x=>1-Math.pow(1-x,3);
const EI=x=>x*x*x;
function fmtES(n,dec){return n.toLocaleString('es-ES',{minimumFractionDigits:dec,maximumFractionDigits:dec});}
function setFrame(i){
  const c=CFG, total=c.total, nin=c.nin, nout=c.nout;
  const p=Math.min(1,i/nin);
  const q=i>=total-nout?Math.min(1,(i-(total-nout)+1)/nout):0;
  const g=document.getElementById('g');
  let tr='', s=1, op=1;
  if(c.kind==='pill'){ s=EB(p); const ty=(1-EC(p))*-160; tr=`translateY(${ty}px) scale(${s*(1-0.1*EI(q))})`; op=Math.min(1,p*2)*(1-EI(q)); }
  else if(c.kind==='end'){ const ty=(1-EC(p))*260; tr=`translateY(${ty}px)`; op=Math.min(1,p*1.6); }
  else { s=EB(p); const rot=(1-EC(p))*-4; tr=`translateY(${(1-EC(p))*70}px) rotate(${rot}deg) scale(${s*(1-0.12*EI(q))})`; op=Math.min(1,p*2)*(1-EI(q)); }
  g.style.transform=tr; g.style.opacity=op;
  if(c.kind==='stat'){ const pp=EC(Math.min(1,i/(nin+c.count||1))); const v=c.from+(c.to-c.from)*pp; document.getElementById('num').textContent=c.pre+fmtES(c.dec?Math.round(v*Math.pow(10,c.dec))/Math.pow(10,c.dec):Math.round(v),c.dec||0)+c.suf; }
  if(c.kind==='bubble'){ const n=Math.floor(EC(Math.min(1,i/(nin+c.type_frames)))*c.text.length); document.getElementById('txt').textContent=c.text.slice(0,n); document.getElementById('cur').style.opacity=(n<c.text.length&&(i%8<5))?1:0; }
  if(c.kind==='list'){ document.querySelectorAll('.it').forEach((el,k)=>{ const st=(c.first||2)+c.step*k; const lp=Math.min(1,Math.max(0,(i-st)/8)); el.style.opacity=lp; el.style.transform=`translateX(${(1-EB(lp))*-60}px)`; }); }
  if(c.kind==='stars'){ document.querySelectorAll('.st').forEach((el,k)=>{ const st=4*k+2; const lp=Math.min(1,Math.max(0,(i-st)/6)); el.style.opacity=lp; el.style.transform=`scale(${EB(lp)})`; }); }
  if(c.kind==='toggle'){ const tp=Math.min(1,Math.max(0,(i-c.off_at)/9)); const kn=document.getElementById('knob'); const tk=document.getElementById('track'); kn.style.transform=`translateX(${(1-EC(tp))*76}px)`; tk.style.background=tp>0.5?'#C7CCD6':'#34C759'; document.getElementById('state').textContent=tp>0.5?'Desactivado':'Activado'; document.getElementById('state').style.color=tp>0.5?'#E5484D':'#1F9D55'; }
}
"""

BASE_CSS = ("html,body{margin:0;background:transparent}"
            "*{box-sizing:border-box}"
            ".wrap{position:relative;width:1080px;height:1920px;font-family:'Inter Tight','Noto Color Emoji',Arial,sans-serif;overflow:hidden}"
            "#g{position:absolute;left:0;right:0;display:flex;justify-content:center;transform-origin:50% 50%;will-change:transform}")


def gfx_html(g):
    e = H.escape; kind = g["kind"]; zone = g.get("zone", "top")
    top = g.get("y", 120 if zone == "top" else LOW_Y - 140)
    if kind == "title":
        kick = f'<div style="font-weight:800;font-size:40px;color:{BLUE};letter-spacing:-0.01em;margin-bottom:10px">{e(g.get("kicker",""))}</div>' if g.get("kicker") else ""
        lines = "<br>".join(e(x) for x in g["lines"])
        inner = (f'<div style="background:{BG};color:{NAVY};border-radius:34px;padding:34px 54px;text-align:center;'
                 f'box-shadow:0 24px 60px rgba(14,21,48,.35);border-left:14px solid {BLUE}">{kick}'
                 f'<div style="font-weight:800;font-size:{g.get("size", 92)}px;line-height:1.0;letter-spacing:-0.045em">{lines}</div></div>')
        top = g.get("y", 1090)
    elif kind == "pill":
        col = g.get("color", "navy")
        bg, fg = {"navy": (NAVY, "#fff"), "blue": (BLUE, "#fff"), "white": (BG, NAVY), "yellow": (YELLOW, NAVY)}[col]
        inner = (f'<div style="background:{bg};color:{fg};border-radius:999px;padding:24px 50px;font-weight:800;'
                 f'font-size:{g.get("size", 60)}px;letter-spacing:-0.03em;box-shadow:0 16px 40px rgba(14,21,48,.35);white-space:nowrap">{e(g["text"])}</div>')
    elif kind == "stat":
        src = f'<div style="margin-top:14px;font-weight:500;font-size:30px;color:#9DBBFF">{e(g["source"])}</div>' if g.get("source") else ""
        inner = (f'<div style="background:{NAVY};color:#fff;border-radius:40px;padding:34px 70px;text-align:center;'
                 f'box-shadow:0 24px 60px rgba(14,21,48,.4);min-width:520px">'
                 f'<div id="num" style="font-weight:800;font-size:{g.get("size", 150)}px;line-height:1;letter-spacing:-0.05em">0</div>'
                 f'<div style="margin-top:10px;font-weight:800;font-size:52px;letter-spacing:-0.02em;color:{YELLOW}">{e(g["label"])}</div>{src}</div>')
    elif kind == "bubble":
        side = g.get("side", "left"); col = g.get("color", "white")
        bg, fg = (BG, NAVY) if col == "white" else (BLUE, "#fff")
        rad = "40px 40px 40px 10px" if side == "left" else "40px 40px 10px 40px"
        just = "flex-start" if side == "left" else "flex-end"
        inner = (f'<div style="width:100%;display:flex;justify-content:{just};padding:0 90px">'
                 f'<div style="background:{bg};color:{fg};border-radius:{rad};padding:32px 46px;font-weight:800;'
                 f'font-size:{g.get("size", 58)}px;line-height:1.1;letter-spacing:-0.03em;max-width:760px;min-height:120px;'
                 f'box-shadow:0 20px 50px rgba(14,21,48,.35)"><span id="txt"></span><span id="cur" style="color:{BLUE if col=="white" else YELLOW}">|</span></div></div>')
    elif kind == "list":
        items = "".join(f'<div class="it" style="display:flex;align-items:center;gap:26px;margin:14px 0;opacity:0">'
                        f'<div style="width:74px;height:74px;border-radius:22px;background:{g.get("mark_bg", "#E5484D")};color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:46px;flex:none">{e(g.get("mark", "✕"))}</div>'
                        f'<div style="font-weight:800;font-size:{g.get("size", 60)}px;letter-spacing:-0.03em;color:{NAVY}">{e(x)}</div></div>' for x in g["items"])
        inner = (f'<div style="background:{BG};border-radius:40px;padding:34px 60px;box-shadow:0 24px 60px rgba(14,21,48,.35);min-width:620px">'
                 + (f'<div style="font-weight:800;font-size:40px;color:{BLUE};margin-bottom:10px">{e(g["title"])}</div>' if g.get("title") else "") + items + '</div>')
    elif kind == "stars":
        n = int(g.get("filled", 1))
        stars = "".join(f'<span class="st" style="display:inline-block;font-size:96px;line-height:1;color:{YELLOW if k < n else "#B9C1D1"};opacity:0;margin:0 6px">★</span>' for k in range(5))
        inner = (f'<div style="background:{BG};border-radius:999px;padding:18px 44px;box-shadow:0 16px 40px rgba(14,21,48,.35);display:flex;align-items:center;gap:20px">{stars}'
                 + (f'<span style="font-weight:800;font-size:54px;color:{NAVY};margin-left:14px;letter-spacing:-0.03em">{e(g["text"])}</span>' if g.get("text") else "") + '</div>')
    elif kind == "toggle":
        inner = (f'<div style="background:{BG};border-radius:40px;padding:38px 56px;box-shadow:0 24px 60px rgba(14,21,48,.35);min-width:820px">'
                 f'<div style="font-weight:800;font-size:38px;color:{BLUE}">{e(g.get("title", "Ajustes › Controles de datos"))}</div>'
                 f'<div style="display:flex;align-items:center;justify-content:space-between;gap:30px;margin-top:18px">'
                 f'<div style="font-weight:800;font-size:54px;letter-spacing:-0.03em;color:{NAVY};line-height:1.1;max-width:560px">{e(g["text"])}</div>'
                 f'<div id="track" style="width:160px;height:84px;border-radius:999px;background:#34C759;position:relative;flex:none;transition:none">'
                 f'<div id="knob" style="position:absolute;top:6px;left:6px;width:72px;height:72px;border-radius:50%;background:#fff;box-shadow:0 4px 12px rgba(0,0,0,.25);transform:translateX(76px)"></div></div></div>'
                 f'<div id="state" style="margin-top:14px;font-weight:800;font-size:40px;color:#1F9D55">Activado</div></div>')
    elif kind == "end":
        inner = (f'<div style="position:absolute;left:0;right:0;bottom:0;height:720px;'
                 f'background:linear-gradient(to bottom, rgba(247,249,252,0) 0, {BG} 200px)"></div>'
                 f'<div style="position:absolute;left:84px;right:84px;bottom:300px;color:{NAVY}">'
                 f'<div style="font-weight:500;font-size:38px;letter-spacing:0.32em">TACTIA</div>'
                 f'<div style="margin-top:18px;font-weight:800;font-size:84px;line-height:1;letter-spacing:-0.045em">'
                 f'Tactia prepara.<br><span style="color:{BLUE}">Tú decides.</span></div>'
                 f'<div style="margin-top:22px;font-weight:500;font-size:40px">@tactia.es</div></div>')
        top = 0
    else:
        raise SystemExit(f"kind desconocido: {kind}")
    style = f"top:{top}px;" + ("height:1920px;" if kind == "end" else "")
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{ff(500)}{ff(800)}{BASE_CSS}</style></head><body>"
            f"<div class='wrap'><div id='g' style='{style}'>{inner}</div></div><script>{JS}</script></body></html>")


def render_gfx_seq(pg, g, outdir, total, nin, nout):
    """Renderiza la secuencia de PNG de un gráfico: entrada animada, mantenimiento (enlaces duros), salida."""
    outdir.mkdir(parents=True, exist_ok=True)
    cfg = {"kind": g["kind"], "total": total, "nin": nin, "nout": nout}
    for k in ("from", "to", "dec", "pre", "suf", "count", "text", "type_frames", "step", "off_at", "first"):
        if k in g:
            cfg[k] = g[k]
    cfg.setdefault("pre", ""); cfg.setdefault("suf", ""); cfg.setdefault("type_frames", 16); cfg.setdefault("step", 7)
    cfg.setdefault("count", 20); cfg.setdefault("off_at", 12)
    html = gfx_html(g).replace("<script>", f"<script>const CFG={json.dumps(cfg, ensure_ascii=False)};")
    f = outdir / "page.html"; f.write_text(html, encoding="utf-8")
    pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(80)
    # fotogramas "vivos": entrada, salida y cualquier animación interna; el resto se enlaza al anterior
    live_until = nin + max(cfg.get("count", 0), cfg.get("type_frames", 0), cfg.get("first", 2) + cfg.get("step", 0) * 8 + 10, cfg.get("off_at", 0) + 10) + 2
    last = None
    for i in range(total):
        p = outdir / f"{i:04d}.png"
        live = i < live_until or i >= total - nout or (g["kind"] == "bubble" and i < live_until + 8)
        if live or last is None:
            pg.evaluate(f"setFrame({i})"); pg.screenshot(path=str(p), omit_background=True); last = p
        else:
            os.link(last, p)


# ---------- subtítulos ----------

GLUE = {"de", "la", "el", "en", "a", "que", "y", "o", "con", "por", "tu", "su", "lo", "los", "las", "un", "una", "al", "del",
        "es", "se", "te", "le", "ya", "no", "me", "mi", "si", "sí,", "más", "va", "ni", "para", "como", "pero", "son", "sin"}


def word_times(chunks):
    out = []
    for a, b, text in chunks:
        words = text.split()
        weights = [len(re.sub(r"[^\wáéíóúñü]", "", w, flags=re.I)) + 1.2 for w in words]
        tot = sum(weights); t = a
        for i, (w, wt) in enumerate(zip(words, weights)):
            d = (b - a) * wt / tot
            out.append((t, t + d, w, i == len(words) - 1)); t += d
    return out


def caption_lines(words, max_words=4, max_chars=24):
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
        if (re.search(r"[.?!:,»]$", w[2]) or w[3]) and len(cur) >= 2 and not is_glue(cur[-1][2]):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    return lines


def ass_time(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(lines, path, low_zones, hide_zones, end_from=1e9):
    def col(x):
        return f"&H00{x[5:7]}{x[3:5]}{x[1:3]}".upper()
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {HGT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,92,{col(YELLOW)},&H00FFFFFF,{col(NAVY)},&H80000000,-1,0,0,0,100,100,-1,0,1,10,3,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for i, ln in enumerate(lines):
        t0 = ln[0][0]; t1 = ln[-1][1]
        if any(a - 0.05 <= t0 <= b for a, b in hide_zones):
            continue
        t1 = min(lines[i + 1][0][0], t1 + 0.6) if i + 1 < len(lines) else t1 + 0.4
        y = CAP_Y_LOW if any(a - 0.05 <= t0 <= b for a, b in low_zones) else CAP_Y
        if t0 >= end_from - 0.05:
            y = 940
        parts = [f"{{\\k{int(round((b - a) * 100))}}}{w}" for (a, b, w, *_) in ln]
        txt = (f"{{\\an5\\pos({W // 2},{y})\\fscx72\\fscy72\\t(0,90,\\fscx108\\fscy108)\\t(90,150,\\fscx100\\fscy100)}}"
               + " ".join(parts))
        ev.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,0,,{txt}")
    path.write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")


# ---------- montaje ----------

VOICE = ("highpass=f=85,lowpass=f=12500,equalizer=f=220:t=q:w=1.3:g=-2,equalizer=f=3200:t=q:w=1.1:g=2.5,"
         "acompressor=threshold=-20dB:ratio=3:attack=8:release=140:makeup=3,deesser=i=0.3,"
         "loudnorm=I=-14:LRA=9:TP=-1.5,aresample=48000")


def main(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    root = pathlib.Path(spec_path).parent
    out_dir = root / spec.get("out_dir", "entregas"); out_dir.mkdir(parents=True, exist_ok=True)
    (BASE / "tmp-montaje").mkdir(exist_ok=True)
    tmp = pathlib.Path(spec["tmp"]) if spec.get("tmp") else pathlib.Path(tempfile.mkdtemp(prefix=f"{spec['name']}-", dir=BASE / "tmp-montaje"))
    tmp.mkdir(parents=True, exist_ok=True); print("tmp:", tmp)
    src = pathlib.Path(spec["clip"])

    info = probe(src)
    vf = []
    if info["trc"] in ("arib-std-b67", "smpte2084"):
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")
    vf += [f"scale={W}:{HGT}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={W}:{HGT}", f"fps={FPS}",
           "eq=contrast=1.07:saturation=1.14:brightness=0.004", "unsharp=5:5:0.4", "vignette=a=PI/7", "format=yuv420p", "setsar=1"]
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

    def render_seg(k):
        a, b = segs[k]; f = tmp / f"seg{k}.mp4"
        if not f.exists():
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(norm),
                 "-vf", zoom_filter(k), "-af", "aresample=48000", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                 "-c:a", "aac", "-b:a", "192k", str(f)])
        return probe(f)["dur"]
    with ThreadPoolExecutor(max_workers=2) as ex:
        seg_dur = list(ex.map(render_seg, range(n)))

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
        k = min(range(n), key=lambda i: min(abs(ti - segs[i][0]), abs(ti - segs[i][1])))
        a, b = segs[k]
        return out_start[k] + (min(max(ti, a), b) - a)

    print("trozos:", [(round(a, 2), round(b, 2)) for a, b in segs])
    print("transiciones:", [x[0] for x in trans])
    print(f"duración final {total:.1f}s (original {dur:.1f}s)")

    # gráficos -> secuencias PNG
    end_s = float(spec.get("end_secs", 3.3)); end_t0 = max(0.0, total - end_s)
    gfx = [dict(g) for g in spec.get("graphics", [])]
    for g in gfx:
        g["o0"], g["o1"] = to_out(g["t0"]), to_out(g["t1"])
    gfx.append({"kind": "end", "zone": "none", "o0": end_t0, "o1": total + 0.5})
    low_zones = [(g["o0"], g["o1"]) for g in gfx if g.get("zone") == "low"]
    hide_zones = [(g["o0"], g["o1"]) for g in gfx if g["kind"] == "title"]
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": HGT})
        for j, g in enumerate(gfx):
            tot = max(8, int(round((g["o1"] - g["o0"]) * FPS)))
            nin = 12 if g["kind"] != "end" else 14
            nout = 0 if g["kind"] == "end" else min(8, tot // 4)
            if g["kind"] == "toggle" and "off_t" in g:
                g["off_at"] = int(round((to_out(g["off_t"]) - g["o0"]) * FPS))
            d = tmp / f"gfx{j}"
            if not (d / f"{tot - 1:04d}.png").exists():
                render_gfx_seq(pg, g, d, tot, nin, nout)
            g["dir"], g["frames"] = d, tot
        b.close()

    # subtítulos
    words = [(to_out(a), to_out(b), w, e) for a, b, w, e in word_times(chunks)]
    ass = tmp / "caps.ass"
    write_ass(caption_lines(words), ass, low_zones, hide_zones, end_from=end_t0)

    # ffmpeg final
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for k in range(n):
        cmd += ["-i", str(tmp / f"seg{k}.mp4")]
    fc = ""
    for k in range(n):
        fc += f"[{k}:v]settb=AVTB,format=yuv420p[v{k}];[{k}:a]asetpts=PTS-STARTPTS[a{k}];"
    lastv, lasta = "v0", "a0"
    for k in range(n - 1):
        name, d = trans[k]
        tname = "fade" if name == "cut" else name
        fc += f"[{lastv}][v{k + 1}]xfade=transition={tname}:duration={d}:offset={out_start[k + 1]:.3f}[x{k}];"
        fc += f"[{lasta}][a{k + 1}]acrossfade=d={d}:c1=tri:c2=tri[y{k}];"
        lastv, lasta = f"x{k}", f"y{k}"
    idx = n
    for j, g in enumerate(gfx):
        cmd += ["-framerate", str(FPS), "-i", str(g["dir"] / "%04d.png")]
        t0, t1 = g["o0"], g["o0"] + g["frames"] / FPS
        fc += f"[{idx}:v]format=rgba,setpts=PTS+{t0:.3f}/TB[o{j}];"
        fc += f"[{lastv}][o{j}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[w{j}];"
        lastv = f"w{j}"; idx += 1
    fc += f"[{lastv}]ass='{ass}'[vout];"
    fc += f"[{lasta}]{VOICE}[aout]"
    out = out_dir / f"{spec['name']}.mp4"
    cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-maxrate", "7M", "-bufsize", "14M", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    (tmp / "cmd.txt").write_text(" ".join(map(str, cmd)))
    run(cmd)
    print("ok", out, f"{probe(out)['dur']:.1f}s", f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1])

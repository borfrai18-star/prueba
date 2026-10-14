"""Monta los Reels de Borja (grabados con su cara) en el estilo de Tactia.

Uso:  python3 montar_video.py idea.json
idea.json:
{
  "id": "D1A",                          # nombre base de los vídeos
  "clips": ["g1.mov", "g2.mov", "g3.mov", "cuerpo.mov", "final.mov"],
                                        # 1-3 ganchos + cuerpo + final (noticia exprés: 1 gancho)
                                        # o "clips_dir": carpeta con los clips (se ordenan por fecha de grabación)
  "firma": "firmas/F2.mov",             # opcional: firma de 3-5 s grabada una vez
  "hook_texts": ["Texto gancho 1", "Texto gancho 2", "Texto gancho 3"],
  "body_texts": ["Frase 1", "Frase 2", "Frase 3"],   # se reparten a lo largo del cuerpo
  "out_dir": "out"
}
Salida: out/<id>-g1.mp4, -g2.mp4, -g3.mp4 (1080x1920, 30 fps, H.264 + AAC, volumen normalizado).
Recorta silencios al principio y al final de cada clip, convierte HDR de iPhone a SDR,
pone el gancho en texto arriba, las frases clave abajo y la tarjeta de Tactia durante la firma.
"""
import json, sys, subprocess, pathlib, tempfile, html as H, re
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
FONTS = BASE / "node_modules/@fontsource/inter-tight/files"
BLUE, NAVY, BG = "#1463FF", "#0E1530", "#F7F9FC"
W, HGT, FPS = 1080, 1920, 30


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"Falló: {' '.join(map(str, cmd))[:300]}\n{r.stderr[-2000:]}")
    return r


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    tags = d.get("format", {}).get("tags", {})
    created = tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time") or ""
    return {"dur": float(d["format"]["duration"]), "trc": (v or {}).get("color_transfer", ""),
            "has_audio": a is not None, "created": created}


def speech_bounds(path, dur):
    """Devuelve (inicio, fin) de la parte hablada, quitando silencios de los extremos."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-35dB:d=0.25",
                        "-vn", "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    a, b = 0.0, dur
    if starts and starts[0] <= 0.05 and ends:
        a = max(0.0, ends[0] - 0.08)
    if starts and (len(ends) < len(starts) or (ends and ends[-1] >= dur - 0.05)):
        b = min(dur, starts[-1] + 0.15)
    if b - a < 0.6:  # por si el clip es casi todo silencio: no recortar
        a, b = 0.0, dur
    return a, b


def normalize(src, dst, tmp, hflip=False):
    info = probe(src)
    a, b = speech_bounds(src, info["dur"]) if info["has_audio"] else (0.0, info["dur"])
    vf = []
    if info["trc"] in ("arib-std-b67", "smpte2084"):
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
                  "zscale=t=bt709:m=bt709:r=tv")
    if hflip:
        vf.append("hflip")
    vf += [f"scale={W}:{HGT}:force_original_aspect_ratio=increase", f"crop={W}:{HGT}", f"fps={FPS}",
           "format=yuv420p", "setsar=1"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", str(src)]
    if not info["has_audio"]:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest"]
    cmd += ["-vf", ",".join(vf), "-af" if info["has_audio"] else "-filter:a", "aresample=48000",
            "-ac", "2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", str(dst)]
    run(cmd)
    return probe(dst)["dur"]


def ff(w):
    return (f"@font-face{{font-family:'Inter Tight';font-weight:{w};"
            f"src:url('file://{FONTS}/inter-tight-latin-{w}-normal.woff2') format('woff2');}}")


def card_html(kind, text=""):
    e = H.escape
    if kind == "hook":
        inner = (f'<div style="position:absolute;left:70px;right:70px;top:250px;display:flex;justify-content:center">'
                 f'<div style="background:{BG};color:{NAVY};border-radius:28px;padding:30px 40px;'
                 f'font-weight:800;font-size:70px;line-height:1.05;letter-spacing:-0.035em;text-align:center;'
                 f'box-shadow:0 10px 40px rgba(14,21,48,.25)">{e(text)}</div></div>')
    elif kind == "point":
        inner = (f'<div style="position:absolute;left:80px;right:80px;top:1230px;display:flex;justify-content:center">'
                 f'<div style="background:{BLUE};color:#fff;border-radius:22px;padding:22px 34px;'
                 f'font-weight:800;font-size:56px;line-height:1.08;letter-spacing:-0.03em;text-align:center">{e(text)}</div></div>')
    else:  # end card
        inner = (f'<div style="position:absolute;left:0;right:0;bottom:0;height:760px;'
                 f'background:linear-gradient(to bottom, rgba(247,249,252,0) 0, {BG} 180px)"></div>'
                 f'<div style="position:absolute;left:84px;right:84px;bottom:430px;color:{NAVY}">'
                 f'<div style="font-weight:500;font-size:40px;letter-spacing:0.32em">TACTIA</div>'
                 f'<div style="margin-top:22px;font-weight:800;font-size:84px;line-height:1;letter-spacing:-0.045em">'
                 f'Tactia prepara.<br><span style="color:{BLUE}">Tú decides.</span></div>'
                 f'<div style="margin-top:26px;font-weight:500;font-size:40px">@tactia.es</div></div>')
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{ff(500)}{ff(800)}"
            f"html,body{{margin:0;background:transparent}}</style></head><body>"
            f"<div style=\"position:relative;width:{W}px;height:{HGT}px;font-family:'Inter Tight',Arial,sans-serif\">{inner}</div>"
            f"</body></html>")


def render_cards(cards, tmp):
    """cards: lista de (nombre, kind, texto) -> rutas PNG transparentes."""
    paths = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": HGT})
        for name, kind, text in cards:
            f = tmp / f"{name}.html"
            f.write_text(card_html(kind, text), encoding="utf-8")
            pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(150)
            p = tmp / f"{name}.png"
            pg.screenshot(path=str(p), omit_background=True)
            paths[name] = p
        b.close()
    return paths


def assemble(parts, overlays, out):
    """parts: clips normalizados en orden. overlays: lista de (png, t0, t1)."""
    total = sum(probe(p)["dur"] for p in parts) + 0.5
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for p in parts:
        cmd += ["-i", str(p)]
    for png, _, _ in overlays:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.2f}", "-i", str(png)]
    n = len(parts)
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v0][a0];"
    last = "v0"
    for k, (_, t0, t1) in enumerate(overlays):
        fc += (f"[{last}][{n + k}:v]overlay=0:0:shortest=1:eof_action=pass:"
               f"enable='between(t,{t0:.2f},{t1:.2f})'[v{k + 1}];")
        last = f"v{k + 1}"
    fc += "[a0]loudnorm=I=-14:LRA=11:TP=-1.5,aresample=48000[a]"
    cmd += ["-filter_complex", fc, "-map", f"[{last}]", "-map", "[a]", "-shortest", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    run(cmd)


def main(spec_path):
    spec_path = pathlib.Path(spec_path)
    spec = json.loads(spec_path.read_text())
    root = spec_path.parent
    if "videos" in spec:
        return main_completos(spec, root)
    if "clips" in spec:
        clips = [root / c for c in spec["clips"]]
    else:
        files = [p for p in (root / spec["clips_dir"]).iterdir() if p.suffix.lower() in (".mov", ".mp4", ".m4v")]
        clips = sorted(files, key=lambda p: (probe(p)["created"], p.name))
    nh = len(clips) - 2  # ganchos = todos menos los 2 últimos (cuerpo y final)
    if nh < 1 or nh != len(spec["hook_texts"]):
        raise SystemExit(f"Clips: {[c.name for c in clips]}. Tiene que haber 1-3 ganchos + cuerpo + final, "
                         f"y tantos hook_texts como ganchos ({len(spec['hook_texts'])}).")
    out_dir = root / spec.get("out_dir", "out"); out_dir.mkdir(parents=True, exist_ok=True)
    (BASE / "tmp-montaje").mkdir(exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"{spec['id']}-", dir=BASE / "tmp-montaje"))

    norm, durs = [], []
    for i, c in enumerate(clips):
        d = tmp / f"n{i}.mp4"; durs.append(normalize(c, d, tmp)); norm.append(d)
    firma = None
    if spec.get("firma"):
        firma = tmp / "firma.mp4"; fdur = normalize(root / spec["firma"], firma, tmp)

    cards = [(f"hook{i}", "hook", t) for i, t in enumerate(spec["hook_texts"])]
    cards += [(f"pt{i}", "point", t) for i, t in enumerate(spec.get("body_texts", []))]
    cards.append(("end", "end", ""))
    png = render_cards(cards, tmp)

    body_d, final_d = durs[nh], durs[nh + 1]
    for g in range(nh):
        hook_d = durs[g]
        parts = [norm[g], norm[nh], norm[nh + 1]] + ([firma] if firma else [])
        ov = [(png[f"hook{g}"], 0, hook_d)]
        pts = spec.get("body_texts", [])
        if pts:
            step = body_d / len(pts)
            for i in range(len(pts)):
                t0 = hook_d + i * step + 0.15
                ov.append((png[f"pt{i}"], t0, hook_d + (i + 1) * step - 0.1))
        end_t0 = hook_d + body_d + final_d
        end_t1 = end_t0 + (fdur if firma else 0)
        if firma:
            ov.append((png["end"], end_t0, end_t1))
        else:  # sin firma: la tarjeta de Tactia va encima de la frase final
            ov.append((png["end"], hook_d + body_d, end_t0))
        out = out_dir / f"{spec['id']}-g{g + 1}.mp4"
        assemble(parts, ov, out)
        print("ok", out, f"{probe(out)['dur']:.1f}s")


def main_completos(spec, root):
    """Modo vídeo completo: Borja graba cada vídeo entero (gancho + cuerpo + final) en un solo clip.
    spec: {"id": "S1", "out_dir": "out", "hook_secs": 3.0, "end_secs": 4.0,
           "videos": [{"name": "V01", "clip": "IMG_0001.MOV", "hook_text": "...", "body_texts": ["...", "..."]}, ...]}
    """
    out_dir = root / spec.get("out_dir", "out"); out_dir.mkdir(parents=True, exist_ok=True)
    (BASE / "tmp-montaje").mkdir(exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"{spec.get('id', 'videos')}-", dir=BASE / "tmp-montaje"))
    hook_s, end_s = float(spec.get("hook_secs", 3.0)), float(spec.get("end_secs", 4.0))
    for k, v in enumerate(spec["videos"]):
        n = tmp / f"c{k}.mp4"; dur = normalize(root / v["clip"], n, tmp, hflip=bool(v.get("hflip", spec.get("hflip", False))))
        cards = [(f"h{k}", "hook", v["hook_text"]), (f"e{k}", "end", "")]
        pts = v.get("body_texts", [])
        cards += [(f"p{k}_{i}", "point", t) for i, t in enumerate(pts)]
        png = render_cards(cards, tmp)
        h = min(hook_s, dur * 0.3); e0 = max(h, dur - end_s)
        ov = [(png[f"h{k}"], 0, h)]
        if pts and e0 - h > 1:
            step = (e0 - h) / len(pts)
            ov += [(png[f"p{k}_{i}"], h + i * step + 0.15, h + (i + 1) * step - 0.1) for i in range(len(pts))]
        ov.append((png[f"e{k}"], e0, dur))
        out = out_dir / f"{v['name']}.mp4"
        assemble([n], ov, out)
        print("ok", out, f"{probe(out)['dur']:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1])

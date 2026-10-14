#!/usr/bin/env python3
"""Montaje dinámico de un vídeo grabado a cámara (un clip entero por vídeo).

- Quita las pausas largas (jump cuts) y en cada corte cambia el encuadre (zoom y desplazamiento alternos,
  con un pequeño "golpe" de zoom al entrar y un acercamiento lento durante la frase).
- Gancho arriba (primeros segundos), frases clave abajo con entrada animada, tarjeta de Tactia al final.
- Nada de inversión de imagen: se respeta el lado desde el que se grabó.

Uso: python3 montar_dinamico.py spec.json
spec: {"id":"V1","out_dir":"entregas","hook_secs":3.2,"end_secs":4.0,
       "videos":[{"name":"V01","clip":"/ruta/video.mp4","hook_text":"...","body_texts":["...","..."],
                  "cut_pause":0.3, "keep_pause":0.12}]}
"""
import json, pathlib, re, subprocess, sys, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from montar_video import BASE, FPS, W, HGT, probe, normalize, render_cards, run  # noqa: E402


def silences(path, noise=-30, d=0.15):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise}dB:d={d}",
                        "-vn", "-f", "null", "-"], capture_output=True, text=True)
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(st, en))


def speech_segments(dur, sil, cut_pause=0.3, keep=0.12, min_seg=1.6, split_at=0.18):
    """Trozos (a,b) con voz, quitando las pausas >= cut_pause (deja `keep` s a cada lado)."""
    segs, cur = [], 0.0
    for s, e in sil:
        if s <= 0.1:          # silencio inicial
            cur = max(0.0, e - 0.1); continue
        if e >= dur - 0.1:    # silencio final
            dur = min(dur, s + 0.2); break
        if e - s >= cut_pause:          # pausa larga: se quita (jump cut)
            segs.append((cur, s + keep)); cur = max(cur, e - keep)
        elif e - s >= split_at:         # pausa corta: solo cambia el encuadre, no se quita nada
            m = (s + e) / 2
            segs.append((cur, m)); cur = m
    segs.append((cur, dur))
    # une trozos demasiado cortos con el siguiente
    out = []
    for a, b in segs:
        if out and (out[-1][1] - out[-1][0]) < min_seg:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    if len(out) > 1 and (out[-1][1] - out[-1][0]) < min_seg:
        _, b = out.pop(); out[-1] = (out[-1][0], b)
    return [(round(a, 3), round(b, 3)) for a, b in out if b - a > 0.3]


# encuadres que se alternan en cada corte: (zoom base, desplazamiento x en px sobre 1080, desplazamiento y)
FRAMES = [(1.00, 0, 0), (1.22, 60, -40), (1.10, -50, 0), (1.32, 40, -60), (1.05, 0, 0), (1.25, -60, -40)]


def zoom_expr(k, nframes):
    z0, dx, dy = FRAMES[k % len(FRAMES)]
    drift = 0.0009                      # acercamiento lento durante la frase
    bump = 0.05                         # golpe de zoom al entrar (4 fotogramas)
    z = f"({z0}+{drift}*on+{bump}*max(0\\,1-on/4))"
    x = f"(iw/2-(iw/zoom/2)+{dx}*2)"     # la entrada a zoompan va a 2x, por eso *2
    y = f"(ih/2-(ih/zoom/2)+{dy}*2)"
    return (f"scale={W * 2}:{HGT * 2}:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{HGT}:fps={FPS}")


def build(v, spec, tmp, out_dir):
    hook_s = float(spec.get("hook_secs", 3.2)); end_s = float(spec.get("end_secs", 4.0))
    src = pathlib.Path(v["clip"])
    norm = tmp / "norm.mp4"
    # normaliza (1080x1920, 30 fps, tonemap si hace falta) sin recortar: los cortes los decidimos aquí
    info = probe(src)
    vf = []
    if info["trc"] in ("arib-std-b67", "smpte2084"):
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv")
    vf += [f"scale={W}:{HGT}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={W}:{HGT}", f"fps={FPS}",
           "format=yuv420p", "setsar=1"]
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vf", ",".join(vf),
         "-af", "aresample=48000", "-ac", "2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
         "-c:a", "aac", "-b:a", "192k", str(norm)])
    dur = probe(norm)["dur"]
    segs = speech_segments(dur, silences(norm), v.get("cut_pause", 0.3), v.get("keep_pause", 0.12))
    print("cortes:", segs)

    # tiempos de salida de cada trozo
    starts, t = [], 0.0
    for a, b in segs:
        starts.append(t); t += (b - a)
    total = t
    pts = v.get("body_texts", [])
    cards = [("hook", "hook", v["hook_text"]), ("end", "end", "")] + [(f"p{i}", "point", s) for i, s in enumerate(pts)]
    png = render_cards(cards, tmp)

    h = min(hook_s, total * 0.3); e0 = max(h, total - end_s)
    ov = [(png["hook"], 0.0, h, 0.0)]
    if pts and e0 - h > 1:
        step = (e0 - h) / len(pts)
        for i in range(len(pts)):
            ideal = h + i * step + 0.15
            # engancha el texto al corte más cercano si está a menos de 1 s
            near = min(starts, key=lambda s: abs(s - ideal))
            t0 = near if abs(near - ideal) < 1.0 and near >= h else ideal
            t1 = h + (i + 1) * step - 0.1
            ov.append((png[f"p{i}"], t0, max(t0 + 1.0, t1), 0.22))
    ov.append((png["end"], e0, total + 0.5, 0.35))

    # filtro: trozos con zoom distinto -> concat -> overlays con fundido de entrada
    fc = ""
    for k, (a, b) in enumerate(segs):
        fc += (f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,{zoom_expr(k, int((b - a) * FPS))}[v{k}];"
               f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{k}];")
    fc += "".join(f"[v{k}][a{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[vc][ac];"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(norm)]
    last = "vc"
    for k, (p, t0, t1, fade) in enumerate(ov):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total + 1:.2f}", "-i", str(p)]
        idx = k + 1
        if fade > 0:
            fc += f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d={fade}:alpha=1[o{k}];"
            src_ov = f"o{k}"
        else:
            src_ov = f"{idx}:v"
        fc += (f"[{last}][{src_ov}]overlay=0:0:shortest=1:eof_action=pass:"
               f"enable='between(t,{t0:.2f},{t1:.2f})'[w{k}];")
        last = f"w{k}"
    fc += "[ac]loudnorm=I=-14:LRA=11:TP=-1.5,aresample=48000[a]"
    out = out_dir / f"{v['name']}.mp4"
    cmd += ["-filter_complex", fc, "-map", f"[{last}]", "-map", "[a]", "-shortest", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    run(cmd)
    print("ok", out, f"{probe(out)['dur']:.1f}s", f"(original {dur:.1f}s, {len(segs)} trozos)")


def main(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    root = pathlib.Path(spec_path).parent
    out_dir = root / spec.get("out_dir", "entregas"); out_dir.mkdir(parents=True, exist_ok=True)
    (BASE / "tmp-montaje").mkdir(exist_ok=True)
    for v in spec["videos"]:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"{v['name']}-", dir=BASE / "tmp-montaje"))
        build(v, spec, tmp, out_dir)


if __name__ == "__main__":
    main(sys.argv[1])

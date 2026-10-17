#!/usr/bin/env python3
"""Montaje PRO v4: fondo real (no se toca) + transiciones dinámicas hechas fotograma a fotograma
(barridos con desenfoque de movimiento, zoom con desenfoque radial, giro, glitch, flash, sacudida y
cortes secos con punch), más ritmo de corte (planos largos partidos en dos), y encima todo lo de v2:
título animado del gancho, gráficos animados, subtítulos palabra a palabra, voz tratada. Sin sonidos de
transición: solo la voz.
"""
import json, pathlib, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from montar_video import BASE, FPS, W, HGT, probe, run  # noqa: E402
from montar_pro2 import (segments_from_chunks, render_gfx_seq, word_times, caption_lines, write_ass, VOICE)  # noqa: E402
import transiciones as TR  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

# encuadres alternos con aire por arriba
FRAMES = [(1.00, 0, 0), (1.16, 40, -70), (1.06, -30, -30), (1.22, 20, -90), (1.00, 0, 0), (1.18, -40, -75), (1.10, 30, -50), (1.24, 0, -95)]


def zoom_filter(k):
    z0, dx, dy = FRAMES[k % len(FRAMES)]
    z = f"({z0}+0.0008*on+0.05*max(0\\,1-on/4))"
    return (f"scale={int(W * 1.5)}:{int(HGT * 1.5)}:flags=bicubic,"
            f"zoompan=z='{z}':x='(iw/2-(iw/zoom/2)+{dx * 1.5})':y='(ih/2-(ih/zoom/2)+{dy * 1.5})':d=1:s={W}x{HGT}:fps={FPS},"
            f"settb=AVTB,format=yuv420p")


def split_long(segs, max_len=3.4):
    out = []
    for a, b in segs:
        if b - a > max_len:
            m = (a + b) / 2
            out += [(a, m), (m, b)]
        else:
            out.append((a, b))
    return out


def nframes(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames",
             "-of", "csv=p=0", str(path)])
    return int(r.stdout.strip())


def main(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text())
    root = pathlib.Path(spec_path).parent
    out_dir = root / spec.get("out_dir", "entregas4"); out_dir.mkdir(parents=True, exist_ok=True)
    (BASE / "tmp-montaje").mkdir(exist_ok=True)
    tmp = pathlib.Path(spec["tmp"]) if spec.get("tmp") else pathlib.Path(tempfile.mkdtemp(prefix=f"{spec['name']}-", dir=BASE / "tmp-montaje"))
    tmp.mkdir(parents=True, exist_ok=True); print("tmp:", tmp, flush=True)
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
    segs = segments_from_chunks(chunks, spec.get("cut_pause", 0.45), spec.get("keep_pause", 0.16), spec.get("min_seg", 1.3))
    segs = split_long([(a, min(b, dur)) for a, b in segs], spec.get("max_seg", 3.4))
    n = len(segs)
    cycle = ["cut", "cut", "whipleft", "cut", "cut", "cut", "zoomblur", "cut", "cut", "flash", "cut", "cut", "whipright",
             "cut", "cut", "cut", "shake", "cut", "cut", "whipup"]
    kinds = [cycle[k % len(cycle)] for k in range(n - 1)]
    print("trozos:", [(round(a, 2), round(b, 2)) for a, b in segs])
    print("transiciones:", kinds, flush=True)

    # trozos (fondo real, punch-in alterno)
    def render_seg(k):
        a, b = segs[k]; f = tmp / f"seg{k}.mp4"
        if not f.exists():
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(norm),
                 "-vf", zoom_filter(k), "-af", "aresample=48000", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                 "-c:a", "aac", "-b:a", "192k", str(f)])
        return nframes(f)
    with ThreadPoolExecutor(max_workers=2) as ex:
        seg_frames = list(ex.map(render_seg, range(n)))

    # transiciones (clips cortos que sustituyen fotogramas de los extremos)
    cut = []  # (na, nb) por transición
    for k, kind in enumerate(kinds):
        fn, na, nb = TR.KINDS[kind]
        na = min(na, seg_frames[k] // 3); nb = min(nb, seg_frames[k + 1] // 3)
        if kind == "cut" or na + nb == 0:
            cut.append((0, 0)); continue
        A, _ = TR.read_frames(str(tmp / f"seg{k}.mp4"), -na, na) if na else ([], 0)
        B, _ = TR.read_frames(str(tmp / f"seg{k + 1}.mp4"), 0, nb) if nb else ([], 0)
        na, nb = len(A), len(B)
        frames = fn(A, B)
        TR.write_clip(frames, str(tmp / f"tr{k}.mp4"))
        cut.append((na, nb))
    print("transiciones listas", flush=True)

    out_start = []; t = 0.0
    for k in range(n):
        out_start.append(t); t += seg_frames[k] / FPS
    total = t

    def to_out(ti):
        for k, (a, b) in enumerate(segs):
            if a - 1e-6 <= ti <= b + 1e-6:
                return out_start[k] + (ti - a)
        k = min(range(n), key=lambda i: min(abs(ti - segs[i][0]), abs(ti - segs[i][1])))
        a, b = segs[k]
        return out_start[k] + (min(max(ti, a), b) - a)
    print(f"duración final {total:.1f}s (original {dur:.1f}s)", flush=True)

    # gráficos animados
    end_s = float(spec.get("end_secs", 3.3)); end_t0 = max(0.0, total - end_s)
    gfx = [dict(g) for g in spec.get("graphics", [])]
    for g in gfx:
        g["o0"], g["o1"] = to_out(g["t0"]), to_out(g["t1"])
    gfx.append({"kind": "end", "zone": "none", "o0": end_t0, "o1": total + 0.5})
    low_zones = [(g["o0"], g["o1"]) for g in gfx if g.get("zone") == "low"]
    hide_zones = [(g["o0"], g["o1"]) for g in gfx if g["kind"] in ("title", "impact")]
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": HGT})
        for j, g in enumerate(gfx):
            tot = max(8, int(round((g["o1"] - g["o0"]) * FPS)))
            nin = {"end": 14, "impact": 7}.get(g["kind"], 12)
            nout = 0 if g["kind"] == "end" else min(5 if g["kind"] == "impact" else 8, tot // 4)
            if g["kind"] == "toggle" and "off_t" in g:
                g["off_at"] = int(round((to_out(g["off_t"]) - g["o0"]) * FPS))
            dd = tmp / f"gfx{j}"
            if not (dd / f"{tot - 1:04d}.png").exists():
                render_gfx_seq(pg, g, dd, tot, nin, nout)
            g["dir"], g["frames"] = dd, tot
        b.close()

    # subtítulos
    words = [(to_out(a), to_out(b), w, e) for a, b, w, e in word_times(chunks)]
    ass = tmp / "caps.ass"
    write_ass(caption_lines(words), ass, low_zones, hide_zones, end_from=end_t0)

    # montaje final: vídeo = trozos recortados + clips de transición; audio = trozos enteros
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for k in range(n):
        cmd += ["-i", str(tmp / f"seg{k}.mp4")]
    tr_idx = {}
    idx = n
    for k in range(n - 1):
        if cut[k] != (0, 0):
            cmd += ["-i", str(tmp / f"tr{k}.mp4")]; tr_idx[k] = idx; idx += 1
    fc = ""; vparts = []; aparts = []
    for k in range(n):
        s0 = cut[k - 1][1] if k > 0 else 0
        e0 = seg_frames[k] - (cut[k][0] if k < n - 1 else 0)
        fc += f"[{k}:v]trim=start_frame={s0}:end_frame={e0},setpts=PTS-STARTPTS,settb=AVTB,format=yuv420p[v{k}];"
        d = seg_frames[k] / FPS
        fc += (f"[{k}:a]atrim=0:{d:.4f},asetpts=PTS-STARTPTS,apad=whole_dur={d:.4f},"
               f"afade=t=in:st=0:d=0.012,afade=t=out:st={max(0.0, d - 0.03):.4f}:d=0.03[a{k}];")  # sin chasquidos en los cortes
        vparts.append(f"[v{k}]"); aparts.append(f"[a{k}]")
        if k < n - 1 and k in tr_idx:
            fc += f"[{tr_idx[k]}:v]settb=AVTB,format=yuv420p[t{k}];"
            vparts.append(f"[t{k}]")
    fc += "".join(vparts) + f"concat=n={len(vparts)}:v=1:a=0[vc];"
    fc += "".join(aparts) + f"concat=n={len(aparts)}:v=0:a=1[ac];"
    lastv = "vc"
    for j, g in enumerate(gfx):
        cmd += ["-framerate", str(FPS), "-i", str(g["dir"] / "%04d.png")]
        t0, t1 = g["o0"], g["o0"] + g["frames"] / FPS
        fc += f"[{idx}:v]format=rgba,setpts=PTS+{t0:.3f}/TB[o{j}];"
        fc += f"[{lastv}][o{j}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t1:.3f})'[w{j}];"
        lastv = f"w{j}"; idx += 1
    fc += f"[{lastv}]ass='{ass}'[vout];"
    fc += f"[ac]{VOICE}[aout]"
    out = out_dir / f"{spec['name']}.mp4"
    cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    (tmp / "cmd.txt").write_text(" ".join(map(str, cmd)))
    run(cmd)
    print("ok", out, f"{probe(out)['dur']:.1f}s", f"{out.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])

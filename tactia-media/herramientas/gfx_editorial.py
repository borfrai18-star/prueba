"""Gráficos de estilo editorial (creador profesional): oscuros, finos, sin emojis ni rebotes.

Tipos: label (etiqueta mono + titular serif), card (tarjeta oscura con título mono y texto),
quote (bocadillo minimal), stat (número grande serif + etiqueta mono), list (lista fina numerada), end (cierre).
Animación: aparece con fundido + desenfoque que se aclara + sube 24 px. Sale con fundido.
"""
import html as H, json, os, pathlib

BASE = pathlib.Path(__file__).parent
F = BASE / "node_modules/@fontsource"
W, HGT = 1080, 1920


def faces():
    def ff(name, path, w, style="normal"):
        return f"@font-face{{font-family:'{name}';font-weight:{w};font-style:{style};src:url('file://{path}') format('woff2')}}"
    return (ff("Sans", F / "inter-tight/files/inter-tight-latin-300-normal.woff2", 300)
            + ff("Sans", F / "inter-tight/files/inter-tight-latin-500-normal.woff2", 500)
            + ff("Sans", F / "inter-tight/files/inter-tight-latin-800-normal.woff2", 800)
            + ff("Serif", F / "instrument-serif/files/instrument-serif-latin-400-italic.woff2", 400, "italic")
            + ff("Serif", F / "instrument-serif/files/instrument-serif-latin-400-normal.woff2", 400)
            + ff("Mono", F / "jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff2", 500))


ACC = "#9DBBFF"     # acento suave (azul Tactia aclarado)
CARD = "background:rgba(10,12,20,.62);border:1px solid rgba(255,255,255,.14);border-radius:28px;box-shadow:0 30px 80px rgba(0,0,0,.35)"
MONO = "font-family:Mono;font-size:26px;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.72)"


def em(text):
    """*palabra* -> cursiva serif con acento."""
    e = H.escape(text); out = ""; parts = e.split("*")
    for i, p in enumerate(parts):
        out += (f"<span style=\"font-family:Serif;font-style:italic;font-weight:400;color:{ACC}\">{p}</span>" if i % 2 else p)
    return out


def html(g):
    k = g["kind"]; y = g.get("y", 150)
    if k == "label":
        inner = (f"<div style='padding:0 80px'><div style='{MONO}'><span style='color:{ACC}'>●</span>&nbsp; {H.escape(g['label'])}</div>"
                 + (f"<div style='margin-top:18px;font-family:Sans;font-weight:500;font-size:{g.get('size', 70)}px;line-height:1.02;"
                    f"letter-spacing:-.035em;color:#fff;text-shadow:0 6px 30px rgba(0,0,0,.45)'>{em(g['text'])}</div>" if g.get("text") else "")
                 + "</div>")
    elif k == "card":
        inner = (f"<div style='margin:0 80px;padding:38px 46px;{CARD}'><div style='{MONO}'>{H.escape(g['label'])}</div>"
                 f"<div style='margin-top:16px;font-family:Sans;font-weight:300;font-size:{g.get('size', 62)}px;line-height:1.08;"
                 f"letter-spacing:-.03em;color:#fff'>{em(g['text'])}</div></div>")
    elif k == "quote":
        side = g.get("side", "left")
        inner = (f"<div style='display:flex;justify-content:{'flex-start' if side == 'left' else 'flex-end'};padding:0 80px'>"
                 f"<div style='max-width:760px;padding:30px 40px;{CARD};border-radius:{'28px 28px 28px 8px' if side == 'left' else '28px 28px 8px 28px'}'>"
                 f"<div style='{MONO};font-size:22px'>{H.escape(g.get('label', ''))}</div>"
                 f"<div style='margin-top:10px;font-family:Serif;font-style:italic;font-size:{g.get('size', 66)}px;line-height:1.05;color:#fff'>"
                 f"«{H.escape(g['text'])}»</div></div></div>")
    elif k == "stat":
        inner = (f"<div style='text-align:center'><div id='num' style='font-family:Serif;font-size:{g.get('size', 300)}px;line-height:.9;"
                 f"color:#fff;letter-spacing:-.04em;text-shadow:0 10px 50px rgba(0,0,0,.45)'>{H.escape(g['text'])}</div>"
                 f"<div style='margin-top:6px;{MONO};font-size:30px'>{H.escape(g['label'])}</div></div>")
    elif k == "list":
        rows = "".join(f"<div class='it' style='display:flex;gap:26px;align-items:baseline;padding:18px 0;border-top:1px solid rgba(255,255,255,.12);opacity:0'>"
                       f"<span style='{MONO};font-size:24px;color:{ACC}'>0{i + 1}</span>"
                       f"<span style='font-family:Sans;font-weight:300;font-size:{g.get('size', 54)}px;letter-spacing:-.02em;color:#fff'>{em(t)}</span></div>"
                       for i, t in enumerate(g["items"]))
        inner = f"<div style='margin:0 80px;padding:34px 46px;{CARD}'><div style='{MONO};margin-bottom:10px'>{H.escape(g.get('label', ''))}</div>{rows}</div>"
    elif k == "full":
        bg = {"black": "#070708", "grey": "#D6D6D4"}[g.get("bg", "black")]
        fg = "#F4F4F2" if g.get("bg", "black") == "black" else "#111114"
        lab = (f"<div style='{MONO};color:{'rgba(255,255,255,.55)' if fg != '#111114' else 'rgba(0,0,0,.5)'};margin-bottom:26px'>"
               f"{H.escape(g['label'])}</div>") if g.get("label") else ""
        if g.get("mode") == "number":
            body = (f"<div id='num' style='font-family:Sans;font-weight:800;font-size:{g.get('size', 760)}px;line-height:.8;letter-spacing:-.06em;"
                    f"color:{fg};transform-origin:50% 50%'>{H.escape(g['text'])}</div>"
                    f"<div style='margin-top:40px;font-family:Sans;font-weight:500;font-size:58px;letter-spacing:-.02em;color:{fg}'>{em(g.get('sub', ''))}</div>")
        elif g.get("mode") == "words":
            body = (f"<div style='font-family:Sans;font-weight:500;font-size:{g.get('size', 92)}px;line-height:1.05;letter-spacing:-.04em;color:{fg};padding:0 90px'>"
                    + " ".join(f"<span class='w' style='display:inline-block;opacity:0'>{em(w)}</span>" for w in g["text"].split()) + "</div>")
        else:  # type: máquina de escribir
            body = (f"<div style='font-family:Sans;font-weight:500;font-size:{g.get('size', 70)}px;line-height:1.1;letter-spacing:-.03em;color:{fg};padding:0 100px'>"
                    f"<span id='tw'></span><span id='cur' style='opacity:.6'>|</span></div>")
        if g.get("bg", "black") == "grey":
            body = body.replace(ACC, "#1463FF")
        inner = (f"<div style='position:absolute;inset:0;background:{bg}'></div>"
                 f"<div style='position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center'>"
                 f"{lab}{body}</div>")
        y = 0
    elif k == "end":
        inner = (f"<div style='position:absolute;left:0;right:0;bottom:0;height:900px;background:linear-gradient(to bottom,rgba(6,8,14,0),rgba(6,8,14,.92) 55%)'></div>"
                 f"<div style='position:absolute;left:80px;right:80px;bottom:260px'>"
                 f"<div style='{MONO}'>TACTIA</div>"
                 f"<div style='margin-top:18px;font-family:Sans;font-weight:500;font-size:88px;line-height:1;letter-spacing:-.04em;color:#fff'>"
                 f"Tactia prepara.<br><span style=\"font-family:Serif;font-style:italic;font-weight:400;color:{ACC}\">Tú decides.</span></div>"
                 f"<div style='margin-top:26px;{MONO};font-size:24px'>@tactia.es · un truco de marketing al día</div></div>")
        y = 0
    else:
        raise SystemExit(f"tipo editorial desconocido: {k}")
    full = "height:1920px;" if k in ("end", "full") else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{faces()}html,body{{margin:0;background:transparent}}"
            f"#g{{position:absolute;left:0;right:0;top:{y}px;{full}will-change:transform,opacity,filter}}</style></head><body>"
            f"<div style='position:relative;width:{W}px;height:{HGT}px;overflow:hidden'><div id='g'>{inner}</div></div>"
            "<script>const E=x=>1-Math.pow(1-x,3);"
            "function setFrame(i,c){const p=Math.min(1,i/c.nin);const q=i>=c.total-c.nout?Math.min(1,(i-(c.total-c.nout)+1)/c.nout):0;"
            "const g=document.getElementById('g');const e=E(p);"
            "g.style.opacity=(c.kind==='end'?Math.min(1,p*1.3):e)*(1-q);"
            "g.style.transform=`translateY(${(1-e)*24 - q*10}px)`;g.style.filter=`blur(${(1-e)*10+q*6}px)`;"
            "if(c.kind==='full'){g.style.filter='none';g.style.transform='none';g.style.opacity=Math.min(1,(i+1)/c.nin)*(1-q);"
            "const n=document.getElementById('num');if(n){const t=i/c.total;n.style.transform=`perspective(1400px) rotateY(${-28+16*t}deg) rotateX(${8-4*t}deg) scale(${1.06-0.06*t})`;}"
            "const tw=document.getElementById('tw');if(tw){const L=c.text.length;const k=Math.min(L,Math.floor(L*Math.min(1,i/(c.total*0.55))));tw.textContent=c.text.slice(0,k);"
            "document.getElementById('cur').style.opacity=(k<L||i%16<8)?0.6:0;}"
            "document.querySelectorAll('.w').forEach((el,j)=>{const lp=Math.min(1,Math.max(0,(i-2-j*c.wstep)/6));el.style.opacity=E(lp);el.style.transform=`translateY(${(1-E(lp))*30}px)`;});}"
            "document.querySelectorAll('.it').forEach((el,k)=>{const lp=Math.min(1,Math.max(0,(i-c.first-c.step*k)/9));"
            "el.style.opacity=E(lp);el.style.transform=`translateY(${(1-E(lp))*16}px)`;});}</script></body></html>")


def render(pg, g, outdir, total, nin=10, nout=7):
    outdir.mkdir(parents=True, exist_ok=True)
    f = outdir / "page.html"; f.write_text(html(g), encoding="utf-8")
    pg.goto(f"file://{f}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(100)
    cfg = {"kind": g["kind"], "total": total, "nin": nin, "nout": nout, "first": g.get("first", 4), "step": g.get("step", 8),
           "text": g.get("text", ""), "wstep": g.get("wstep", 4)}
    live_until = total if g["kind"] == "full" else nin + (cfg["first"] + cfg["step"] * 6 + 10 if g["kind"] == "list" else 0) + 1
    last = None
    for i in range(total):
        p = outdir / f"{i:04d}.png"
        if i < live_until or i >= total - nout or last is None:
            pg.evaluate(f"setFrame({i},{json.dumps(cfg)})"); pg.screenshot(path=str(p), omit_background=True); last = p
        else:
            os.link(last, p)
    # todas las imágenes en RGBA (si no, ffmpeg falla al cambiar de formato a mitad de secuencia)
    from PIL import Image
    for p in sorted(outdir.glob("*.png")):
        im = Image.open(p)
        if im.mode != "RGBA":
            im.convert("RGBA").save(p)

// Biblioteca de estilos de animación de Tactia (inspirados en la lista «20 estilos de animación con Claude»).
// Cada estilo es un componente que trabaja con el tiempo local de su <Sequence> (t en segundos).
import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, Fonts } from "../scenes/common";

export const useT = () => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  return {
    f, fps, t: f / fps, width, height,
    sp: (at: number, damping = 14, stiffness = 140) => spring({ frame: f - Math.round(at * fps), fps, config: { damping, stiffness } }),
    lin: (a: number, b: number) => interpolate(f, [a * fps, Math.max(a * fps + 1, b * fps)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  };
};

// pseudoaleatorio estable
const rnd = (i: number) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };

/* ---------- 1. Malla de degradado (fondo vivo) ---------- */
export const GradientMesh: React.FC<{ colors?: string[] }> = ({ colors = ["#1E90FF", "#8B5CF6", "#16B3A6", "#F4C542"] }) => {
  const { t } = useT();
  return (
    <AbsoluteFill style={{ background: "#07080B", overflow: "hidden" }}>
      {colors.map((c, i) => {
        const x = 50 + Math.sin(t * 0.6 + i * 1.7) * 30, y = 45 + Math.cos(t * 0.5 + i * 2.1) * 28;
        return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: 900, height: 900, marginLeft: -450, marginTop: -450, borderRadius: "50%",
          background: `radial-gradient(circle, ${c}cc, transparent 62%)`, filter: "blur(40px)", opacity: .75 }} />;
      })}
      <AbsoluteFill style={{ backgroundImage: "radial-gradient(rgba(255,255,255,.06) 1px, transparent 1px)", backgroundSize: "6px 6px", mixBlendMode: "overlay" }} />
    </AbsoluteFill>
  );
};

/* ---------- 2. Partículas ---------- */
export const Particles: React.FC<{ n?: number; color?: string; converge?: number }> = ({ n = 140, color = "#5ff3e6", converge = 1.2 }) => {
  const { t, width, height } = useT();
  const k = Math.min(1, t / converge);
  const ease = 1 - Math.pow(1 - k, 3);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {Array.from({ length: n }).map((_, i) => {
        const a = rnd(i) * Math.PI * 2, r0 = 900 + rnd(i + 7) * 700, r1 = 120 + rnd(i + 3) * 420;
        const r = r0 + (r1 - r0) * ease, ang = a + t * (0.25 + rnd(i + 9) * 0.5) * (i % 2 ? 1 : -1);
        const s = 3 + rnd(i + 5) * 7;
        return <div key={i} style={{ position: "absolute", left: width / 2 + Math.cos(ang) * r, top: height * 0.45 + Math.sin(ang) * r * 0.75, width: s, height: s, borderRadius: "50%",
          background: color, boxShadow: `0 0 ${s * 3}px ${color}`, opacity: 0.35 + rnd(i + 2) * 0.65 }} />;
      })}
    </AbsoluteFill>
  );
};

/* ---------- 3. Panel de aeropuerto (split-flap) ---------- */
const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
export const SplitFlap: React.FC<{ rows: string[]; at?: number; color?: string; size?: number; top?: number; rowColors?: string[] }> = ({ rows, at = 0, color = "#F7F2EA", size = 96, top = 420, rowColors = [] }) => {
  const { t, width } = useT();
  const longest = Math.max(...rows.map((r) => r.length));
  const sz = Math.min(size, (width - 120) / (longest * 0.86));
  const w = sz * 0.78, h = sz * 1.25;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, top, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
      {rows.map((row, ri) => (
        <div key={ri} style={{ display: "flex", gap: Math.max(4, sz * 0.08) }}>
          {row.split("").map((ch, ci) => {
            const settle = at + 0.35 + ri * 0.5 + ci * 0.07;
            const flipping = t < settle;
            const step = Math.floor(t * 18 + ci * 3 + ri * 5);
            const shown = ch === " " ? " " : flipping ? CHARS[(step + ci * 7) % CHARS.length] : ch;
            const phase = flipping ? (t * 18) % 1 : 0;
            return (
              <div key={ci} style={{ position: "relative", width: w, height: h, borderRadius: 10, background: ch === " " ? "transparent" : "linear-gradient(180deg, #343946 0%, #262a34 49%, #14161c 51%, #1d2029 100%)", border: ch === " " ? "none" : "2px solid rgba(255,255,255,.10)",
                boxShadow: ch === " " ? "none" : "0 10px 24px rgba(0,0,0,.55), inset 0 0 0 2px rgba(255,255,255,.05)", display: "flex", alignItems: "center", justifyContent: "center",
                font: `900 ${sz}px Sans`, color: rowColors[ri] || color, overflow: "hidden", opacity: t < at ? 0 : 1 }}>
                <span style={{ transform: `scaleY(${flipping ? 1 - Math.abs(Math.sin(phase * Math.PI)) * 0.85 : 1})` }}>{shown}</span>
                {ch !== " " && <div style={{ position: "absolute", left: 0, right: 0, top: "50%", height: 2, background: "rgba(0,0,0,.8)" }} />}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
};

/* ---------- 4. Tipografía en movimiento (kinetic type) ---------- */
export const Kinetic: React.FC<{ words: { w: string; at: number; size?: number; color?: string; serif?: boolean }[]; top?: number }> = ({ words, top = 380 }) => {
  const { sp } = useT();
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top }}>
      {words.map((x, i) => {
        const p = sp(x.at, 12, 170);
        return <div key={i} style={{ font: x.serif ? `italic 400 ${x.size ?? 110}px/1.02 Serif` : `900 ${x.size ?? 150}px/0.95 Sans`, letterSpacing: x.serif ? "-.01em" : "-.05em",
          color: x.color ?? "#F7F2EA", opacity: p, transform: `translateX(${(1 - p) * (i % 2 ? 160 : -160)}px) scale(${0.8 + 0.2 * p})`, transformOrigin: "left center",
          filter: `blur(${(1 - p) * 10}px)` }}>{x.w}</div>;
      })}
    </div>
  );
};

/* ---------- 5. Tarjetas de cristal (glassmorphism) ---------- */
export const GlassCards: React.FC<{ cards: { icon: string; title: string; sub: string; at: number }[]; top?: number }> = ({ cards, top = 430 }) => {
  const { sp, t } = useT();
  return (
    <div style={{ position: "absolute", left: 70, right: 70, top, display: "flex", flexDirection: "column", gap: 30 }}>
      {cards.map((c, i) => {
        const p = sp(c.at, 15, 120);
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 34, padding: "30px 36px", borderRadius: 36, background: "rgba(255,255,255,.12)",
            border: "2px solid rgba(255,255,255,.28)", backdropFilter: "blur(26px) saturate(1.4)", boxShadow: "0 30px 60px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.4)",
            opacity: p, transform: `translateY(${(1 - p) * 120}px) rotate(${(1 - p) * (i % 2 ? 4 : -4)}deg) translateY(${Math.sin(t * 1.4 + i) * 6}px)` }}>
            <Img src={staticFile(`icons/${c.icon}.webp`)} style={{ width: 130, height: 130, filter: "drop-shadow(0 18px 24px rgba(0,0,0,.45))" }} />
            <div>
              <div style={{ font: "900 60px/1 Sans", color: "#fff", letterSpacing: "-.03em" }}>{c.title}</div>
              <div style={{ font: "600 36px/1.2 Sans", color: "rgba(255,255,255,.85)", marginTop: 10 }}>{c.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

/* ---------- 6. Neón ---------- */
export const Neon: React.FC<{ text: string; at?: number; color?: string; size?: number; top?: number }> = ({ text, at = 0, color = "#FF3EA5", size = 120, top = 520 }) => {
  const { t } = useT();
  const lt = t - at;
  const on = lt < 0 ? 0 : lt < 0.5 ? (Math.sin(lt * 60) > 0.2 ? 1 : 0.25) : 1;
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top, textAlign: "center", font: `900 ${size}px/1.02 Sans`, letterSpacing: "-.02em", color: on > 0.5 ? "#fff" : color,
      textShadow: `0 0 6px #fff, 0 0 18px ${color}, 0 0 42px ${color}, 0 0 90px ${color}`, opacity: on }}>{text}</div>
  );
};

/* ---------- 7. VHS / directo ---------- */
export const VHS: React.FC<{ children?: React.ReactNode; label?: string }> = ({ children, label = "● EN DIRECTO" }) => {
  const { t, f } = useT();
  const jitter = Math.sin(f * 2.3) * 3;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `translateX(${jitter}px)` }}>{children}</AbsoluteFill>
      <AbsoluteFill style={{ backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,.28) 0 2px, transparent 2px 5px)", mixBlendMode: "multiply" }} />
      <div style={{ position: "absolute", left: 0, right: 0, top: `${(t * 35) % 100}%`, height: 60, background: "linear-gradient(rgba(255,255,255,0),rgba(255,255,255,.08),rgba(255,255,255,0))" }} />
      <div style={{ position: "absolute", right: 60, top: 60, font: "800 34px Sans", color: "#ff4040", letterSpacing: ".18em", opacity: Math.floor(t * 2) % 2 ? 1 : 0.35, textShadow: "0 0 12px #ff4040" }}>{label}</div>
    </AbsoluteFill>
  );
};

/* ---------- 8. Cómic (golpe de sorpresa) ---------- */
export const ComicBurst: React.FC<{ text: string; at?: number; top?: number; color?: string }> = ({ text, at = 0, top = 260, color = "#FFD43B" }) => {
  const { sp } = useT();
  const p = sp(at, 8, 220);
  const pts = Array.from({ length: 24 }).map((_, i) => { const a = (i / 24) * Math.PI * 2, r = i % 2 ? 50 : 34; return `${50 + Math.cos(a) * r}% ${50 + Math.sin(a) * r}%`; }).join(",");
  return (
    <div style={{ position: "absolute", left: "50%", top, width: 640, height: 400, marginLeft: -320, transform: `scale(${p}) rotate(-6deg)` }}>
      <div style={{ position: "absolute", inset: 0, background: color, clipPath: `polygon(${pts})`, filter: "drop-shadow(8px 10px 0 #111)" }} />
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", font: "900 104px Sans", color: "#E5252A",
        WebkitTextStroke: "6px #111", letterSpacing: "-.02em" }}>{text}</div>
    </div>
  );
};

/* ---------- Transición líquida (liquid morph) ---------- */
export const LiquidIn: React.FC<{ start: number; dur?: number; children: React.ReactNode }> = ({ start, dur = 0.6, children }) => {
  const { t } = useT();
  const k = interpolate(t, [start, start + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (k <= 0) return null;
  const e = 1 - Math.pow(1 - k, 3);
  const R = e * 150; // % del tamaño
  const pts = Array.from({ length: 72 }).map((_, i) => {
    const a = (i / 72) * Math.PI * 2;
    const r = R * (1 + 0.09 * Math.sin(5 * a + t * 9) + 0.05 * Math.sin(9 * a - t * 7)) * (k < 1 ? 1 : 3);
    return `${50 + Math.cos(a) * r}% ${55 + Math.sin(a) * r * 0.8}%`;
  }).join(",");
  return <AbsoluteFill style={{ clipPath: k < 1 ? `polygon(${pts})` : undefined }}>{children}</AbsoluteFill>;
};

export const Base: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: "#07080B", overflow: "hidden", fontFamily: "Sans" }}><Fonts />{children}</AbsoluteFill>
);

export const Marca: React.FC<{ text?: string }> = ({ text = "TACTIA · NOTICIAS IA" }) => (
  <div style={{ position: "absolute", left: 60, bottom: 50, font: "800 26px Sans", letterSpacing: ".3em", color: "rgba(255,255,255,.7)" }}>{text}</div>
);

/* =====================  LOS 11 ESTILOS QUE FALTABAN  ===================== */

// rasteriza un texto a una rejilla (para ASCII y pixel art)
const useMask = (text: string, cols: number, rows: number, font: string) =>
  React.useMemo(() => {
    const c = document.createElement("canvas"); c.width = cols; c.height = rows; const g = c.getContext("2d")!;
    g.fillStyle = "#000"; g.fillRect(0, 0, cols, rows); g.fillStyle = "#fff"; g.font = font; g.textAlign = "center"; g.textBaseline = "middle";
    const lines = text.split("\n"); lines.forEach((l, i) => g.fillText(l, cols / 2, rows / 2 + (i - (lines.length - 1) / 2) * rows / (lines.length + 0.4)));
    const d = g.getImageData(0, 0, cols, rows).data; const out: number[] = [];
    for (let i = 0; i < cols * rows; i++) out.push(d[i * 4] / 255);
    return out;
  }, [text, cols, rows, font]);

/* ---------- 9. Holográfico ---------- */
export const Holographic: React.FC<{ text: string; sub?: string; top?: number }> = ({ text, sub, top = 420 }) => {
  const { t, sp } = useT(); const p = sp(0.1, 14, 120);
  const ang = t * 120;
  return (
    <div style={{ position: "absolute", left: 90, right: 90, top, height: 560, borderRadius: 48, overflow: "hidden", transform: `perspective(1400px) rotateX(${12 - p * 6}deg) rotateY(${Math.sin(t * 1.2) * 14}deg) scale(${0.85 + 0.15 * p})`,
      background: `conic-gradient(from ${ang}deg at 50% 50%, #ff9ad5, #9ae6ff, #c7ff9a, #fff59a, #d29aff, #ff9ad5)`, boxShadow: "0 40px 90px rgba(150,120,255,.45)", opacity: p }}>
      <AbsoluteFill style={{ background: "repeating-linear-gradient(115deg, rgba(255,255,255,.0) 0 18px, rgba(255,255,255,.22) 18px 20px)", mixBlendMode: "overlay" }} />
      <div style={{ position: "absolute", top: 0, bottom: 0, width: 260, left: `${((t * 45) % 160) - 30}%`, background: "linear-gradient(90deg,transparent,rgba(255,255,255,.75),transparent)", transform: "skewX(-20deg)", mixBlendMode: "soft-light" }} />
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#1b1530" }}>
        <div style={{ font: "900 130px/1 Sans", letterSpacing: "-.04em", mixBlendMode: "multiply" }}>{text}</div>
        {sub && <div style={{ font: "800 40px Sans", letterSpacing: ".2em", marginTop: 20, opacity: .7 }}>{sub}</div>}
      </div>
    </div>
  );
};

/* ---------- 10. Wireframe 3D ---------- */
export const Wireframe3D: React.FC<{ color?: string; size?: number; top?: number }> = ({ color = "#5ff3e6", size = 420, top = 330 }) => {
  const { t, width } = useT();
  // icosaedro subdividido una vez (esfera en malla)
  const geo = React.useMemo(() => {
    const ph = (1 + Math.sqrt(5)) / 2;
    let v: number[][] = [[-1, ph, 0], [1, ph, 0], [-1, -ph, 0], [1, -ph, 0], [0, -1, ph], [0, 1, ph], [0, -1, -ph], [0, 1, -ph], [ph, 0, -1], [ph, 0, 1], [-ph, 0, -1], [-ph, 0, 1]];
    let f = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]];
    const norm = (a: number[]) => { const l = Math.hypot(a[0], a[1], a[2]); return a.map((x) => x / l); };
    v = v.map(norm); const cache = new Map<string, number>();
    const mid = (a: number, b: number) => { const k = a < b ? `${a}-${b}` : `${b}-${a}`; if (cache.has(k)) return cache.get(k)!; const m = norm([(v[a][0] + v[b][0]) / 2, (v[a][1] + v[b][1]) / 2, (v[a][2] + v[b][2]) / 2]); v.push(m); cache.set(k, v.length - 1); return v.length - 1; };
    const nf: number[][] = []; f.forEach(([a, b, c]) => { const ab = mid(a, b), bc = mid(b, c), ca = mid(c, a); nf.push([a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]); }); f = nf;
    const e = new Set<string>(); f.forEach(([a, b, c]) => [[a, b], [b, c], [c, a]].forEach(([x, y]) => e.add(x < y ? `${x}-${y}` : `${y}-${x}`)));
    return { v, e: [...e].map((s) => s.split("-").map(Number)) };
  }, []);
  const ry = t * 0.7, rx = 0.4 + Math.sin(t * 0.5) * 0.2;
  const P = geo.v.map(([x, y, z]) => { const x1 = x * Math.cos(ry) + z * Math.sin(ry), z1 = -x * Math.sin(ry) + z * Math.cos(ry); const y1 = y * Math.cos(rx) - z1 * Math.sin(rx), z2 = y * Math.sin(rx) + z1 * Math.cos(rx); const s = 3 / (4 - z2); return [width / 2 + x1 * size * s * 0.6, top + size / 2 + y1 * size * s * 0.6, z2]; });
  return (
    <svg width={width} height={top + size + 200} style={{ position: "absolute", left: 0, top: 0 }}>
      {geo.e.map(([a, b], i) => { const z = (P[a][2] + P[b][2]) / 2; return <line key={i} x1={P[a][0]} y1={P[a][1]} x2={P[b][0]} y2={P[b][1]} stroke={color} strokeWidth={1.2 + (z + 1) * 1.2} opacity={0.25 + (z + 1) * 0.35} style={{ filter: `drop-shadow(0 0 6px ${color})` }} />; })}
    </svg>
  );
};

/* ---------- 11. Isométrico (columnas que crecen) ---------- */
export const Isometric: React.FC<{ bars: { v: number; label: string; color: string }[]; top?: number; at?: number }> = ({ bars, top = 860, at = 0 }) => {
  const { sp, width } = useT();
  const max = Math.max(...bars.map((b) => b.v));
  const cx = width / 2 - ((bars.length - 1) * 170) / 2;
  return (
    <svg width={width} height={top + 260} style={{ position: "absolute", left: 0, top: 0 }}>
      {bars.map((b, i) => {
        const p = sp(at + i * 0.18, 13, 110); const h = (b.v / max) * 420 * p; const x = cx + i * 170, y = top - i * 0; const w = 70;
        const shade = (c: string, k: number) => `color-mix(in srgb, ${c} ${k}%, black)`;
        return (
          <g key={i}>
            <polygon points={`${x},${y} ${x + w},${y - w / 2} ${x + w},${y - w / 2 - h} ${x},${y - h}`} fill={shade(b.color, 75)} />
            <polygon points={`${x},${y} ${x - w},${y - w / 2} ${x - w},${y - w / 2 - h} ${x},${y - h}`} fill={b.color} />
            <polygon points={`${x},${y - h} ${x + w},${y - w / 2 - h} ${x},${y - w - h} ${x - w},${y - w / 2 - h}`} fill={shade(b.color, 125)} style={{ filter: "brightness(1.25)" }} />
            <text x={x} y={y + 70} textAnchor="middle" style={{ font: "800 34px Sans", fill: "#fff" }}>{b.label}</text>
          </g>
        );
      })}
    </svg>
  );
};

/* ---------- 12. Plastilina 3D (clay) ---------- */
export const Clay3D: React.FC<{ items: { label: string; color: string }[]; top?: number }> = ({ items, top = 470 }) => {
  const { sp, t } = useT();
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 36 }}>
      {items.map((it, i) => {
        const p = sp(0.15 + i * 0.15, 7, 150);
        return <div key={i} style={{ padding: "40px 56px", borderRadius: 999, background: it.color, color: "#2b2236", font: "900 64px Sans", letterSpacing: "-.02em",
          boxShadow: `inset -14px -18px 28px rgba(0,0,0,.18), inset 14px 16px 26px rgba(255,255,255,.65), 0 26px 40px rgba(60,40,90,.28)`,
          transform: `scale(${p}) translateY(${Math.sin(t * 2 + i) * 8}px) rotate(${(i % 2 ? 3 : -3) * (1 - p)}deg)` }}>{it.label}</div>;
      })}
    </div>
  );
};

/* ---------- 13. Arte ASCII ---------- */
export const AsciiArt: React.FC<{ text: string; top?: number; color?: string }> = ({ text, top = 380, color = "#5ff3e6" }) => {
  const { t, width } = useT();
  const cols = 64, rows = 30; const m = useMask(text, cols, rows, "900 22px Sans");
  const ramp = " .:-=+*#%@";
  const reveal = Math.min(1, t / 1.2);
  const lines: string[] = [];
  for (let r = 0; r < rows; r++) { let s = ""; for (let c = 0; c < cols; c++) { const v = m[r * cols + c]; const noise = Math.sin(c * 1.7 + r * 2.3 + t * 9) * 0.5 + 0.5;
    s += (c / cols) < reveal * 1.2 - r * 0.004 ? ramp[Math.min(9, Math.floor(v * 9 + (v > 0.1 ? noise * 1.5 : 0)))] : (noise > 0.93 ? "·" : " "); } lines.push(s); }
  return <pre style={{ position: "absolute", left: 0, width, top, margin: 0, textAlign: "center", font: `700 ${Math.floor(width / cols / 0.6)}px/1.0 monospace`, color, textShadow: `0 0 8px ${color}` }}>{lines.join("\n")}</pre>;
};

/* ---------- 14. Semitono (halftone) ---------- */
export const Halftone: React.FC<{ text: string; color?: string; bg?: string; top?: number }> = ({ text, color = "#E5252A", bg = "#F4E9D8", top = 380 }) => {
  const { t, width, height } = useT();
  const cell = 22 + Math.sin(t * 2) * 4;
  return (
    <AbsoluteFill style={{ background: bg }}>
      <AbsoluteFill style={{ backgroundImage: `radial-gradient(circle at center, ${color} 0 ${cell * 0.32}px, transparent ${cell * 0.34}px)`, backgroundSize: `${cell}px ${cell}px`,
        WebkitMaskImage: `radial-gradient(circle at ${50 + Math.sin(t) * 20}% ${40 + Math.cos(t * .8) * 15}%, #000 0%, transparent 60%)`, opacity: .9 }} />
      <div style={{ position: "absolute", left: 70, right: 70, top, font: "900 150px/0.92 Sans", letterSpacing: "-.05em", color: "#111", textShadow: `10px 10px 0 ${color}` }}>{text}</div>
    </AbsoluteFill>
  );
};

/* ---------- 15. Bauhaus ---------- */
export const Bauhaus: React.FC<{ text: string; top?: number }> = ({ text, top = 860 }) => {
  const { sp, width } = useT();
  const a = sp(0.1, 10, 120), b = sp(0.3, 10, 120), c = sp(0.5, 10, 120), d = sp(0.8, 14, 140);
  return (
    <AbsoluteFill style={{ background: "#EFE6D2" }}>
      <div style={{ position: "absolute", left: 90, top: 200, width: 420, height: 420, borderRadius: "50%", background: "#E5252A", transform: `translateX(${(1 - a) * -600}px)` }} />
      <div style={{ position: "absolute", right: 80, top: 160, width: 0, height: 0, borderLeft: "230px solid transparent", borderRight: "230px solid transparent", borderBottom: "400px solid #F4C542", transform: `translateY(${(1 - b) * -700}px)` }} />
      <div style={{ position: "absolute", left: 380, top: 470, width: 330, height: 330, background: "#1E4DB7", transform: `rotate(${(1 - c) * 180}deg) scale(${c})` }} />
      <div style={{ position: "absolute", left: 0, top: 640, width: width * d, height: 26, background: "#111" }} />
      <div style={{ position: "absolute", left: 80, right: 80, top, font: "900 120px/0.95 Sans", color: "#111", letterSpacing: "-.04em", textTransform: "uppercase", opacity: d }}>{text}</div>
    </AbsoluteFill>
  );
};

/* ---------- 16. Pixel art ---------- */
export const PixelArt: React.FC<{ text: string; top?: number; color?: string }> = ({ text, top = 420, color = "#3DDC84" }) => {
  const { t, width } = useT();
  const cols = 48, rows = 20; const m = useMask(text, cols, rows, "900 15px monospace");
  const px = Math.floor((width - 120) / cols); const shown = Math.floor(Math.min(1, t / 1.0) * cols * rows);
  return (
    <AbsoluteFill style={{ background: "#120d24" }}>
      <AbsoluteFill style={{ backgroundImage: "linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px),linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px)", backgroundSize: `${px}px ${px}px` }} />
      <div style={{ position: "absolute", left: (width - px * cols) / 2, top, display: "grid", gridTemplateColumns: `repeat(${cols}, ${px}px)` }}>
        {m.map((v, i) => <div key={i} style={{ width: px, height: px, background: v > 0.45 && i < shown ? color : "transparent", boxShadow: v > 0.45 && i < shown ? `inset -3px -3px 0 rgba(0,0,0,.35)` : "none" }} />)}
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: top + px * rows + 60, textAlign: "center", font: "800 40px monospace", color: "#F4C542", opacity: Math.floor(t * 2) % 2 ? 1 : 0.2 }}>PRESS START ▶</div>
    </AbsoluteFill>
  );
};

/* ---------- 17. Plano técnico (blueprint) ---------- */
export const Blueprint: React.FC<{ title: string; top?: number }> = ({ title, top = 300 }) => {
  const { lin, width } = useT();
  const d = lin(0.1, 1.6);
  const L = 2400;
  return (
    <AbsoluteFill style={{ background: "#0d3b8a", backgroundImage: "linear-gradient(rgba(255,255,255,.12) 1px, transparent 1px),linear-gradient(90deg, rgba(255,255,255,.12) 1px, transparent 1px),linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)", backgroundSize: "120px 120px,120px 120px,24px 24px,24px 24px" }}>
      <svg width={width} height={1300} style={{ position: "absolute", left: 0, top: 0 }}>
        <g fill="none" stroke="#fff" strokeWidth={4} strokeDasharray={L} strokeDashoffset={L * (1 - d)}>
          <rect x={290} y={top + 120} width={500} height={330} rx={30} />
          <rect x={330} y={top + 160} width={420} height={230} rx={12} />
          <line x1={540} y1={top + 450} x2={540} y2={top + 520} /><line x1={440} y1={top + 520} x2={640} y2={top + 520} />
          <circle cx={540} cy={top + 275} r={60} />
        </g>
        <g stroke="#9cc4ff" strokeWidth={2} opacity={d}>
          <line x1={290} y1={top + 80} x2={790} y2={top + 80} /><line x1={290} y1={top + 66} x2={290} y2={top + 94} /><line x1={790} y1={top + 66} x2={790} y2={top + 94} />
          <line x1={840} y1={top + 120} x2={840} y2={top + 450} /><line x1={826} y1={top + 120} x2={854} y2={top + 120} /><line x1={826} y1={top + 450} x2={854} y2={top + 450} />
        </g>
        <text x={540} y={top + 64} textAnchor="middle" style={{ font: "700 26px monospace", fill: "#cfe2ff", opacity: d }}>500 px</text>
        <text x={870} y={top + 290} style={{ font: "700 26px monospace", fill: "#cfe2ff", opacity: d }}>330</text>
      </svg>
      <div style={{ position: "absolute", left: 70, right: 70, top: top + 600, font: "800 76px/1.05 monospace", color: "#fff", letterSpacing: "-.02em", opacity: d }}>{title}</div>
      <div style={{ position: "absolute", right: 70, bottom: 120, padding: "16px 24px", border: "3px solid #fff", font: "700 24px monospace", color: "#fff", lineHeight: 1.5 }}>PLANO N.º 01<br />TACTIA · ESC. 1:1</div>
    </AbsoluteFill>
  );
};

/* ---------- 18. Art déco ---------- */
export const ArtDeco: React.FC<{ text: string; sub?: string; top?: number }> = ({ text, sub, top = 560 }) => {
  const { lin, width, height } = useT();
  const d = lin(0.05, 1.2); const gold = "#D4AF37";
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #1b1712, #070605 75%)" }}>
      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: 36 }).map((_, i) => { const a = (i / 36) * Math.PI * 2; return <line key={i} x1={width / 2} y1={top} x2={width / 2 + Math.cos(a) * 900 * d} y2={top + Math.sin(a) * 900 * d} stroke={gold} strokeWidth={i % 3 ? 1 : 3} opacity={.35} />; })}
        <rect x={110} y={top - 230} width={width - 220} height={460} fill="#0b0907" stroke={gold} strokeWidth={4} />
        <rect x={130} y={top - 210} width={width - 260} height={420} fill="none" stroke={gold} strokeWidth={1.5} />
        {[0, 1].map((k) => <polygon key={k} points={`${width / 2 - 60},${top + (k ? 230 : -230)} ${width / 2},${top + (k ? 290 : -290)} ${width / 2 + 60},${top + (k ? 230 : -230)}`} fill={gold} />)}
      </svg>
      <div style={{ position: "absolute", left: 140, right: 140, top: top - 110, textAlign: "center", font: "italic 400 130px/1 Serif", color: gold, letterSpacing: ".02em", opacity: d, textShadow: "0 0 30px rgba(212,175,55,.35)" }}>{text}</div>
      {sub && <div style={{ position: "absolute", left: 140, right: 140, top: top + 70, textAlign: "center", font: "800 30px Sans", letterSpacing: ".5em", color: "#efe2b8", opacity: d }}>{sub}</div>}
    </AbsoluteFill>
  );
};

/* ---------- 19. Neobrutalismo ---------- */
export const NeoBrutal: React.FC<{ title: string; items: string[]; top?: number }> = ({ title, items, top = 300 }) => {
  const { sp } = useT();
  const cols = ["#FFD43B", "#7CF5C4", "#FF8FB1", "#8EC5FF"];
  return (
    <AbsoluteFill style={{ background: "#FFF4E0" }}>
      <div style={{ position: "absolute", left: 70, right: 70, top, padding: "26px 34px", background: "#fff", border: "6px solid #111", boxShadow: "14px 14px 0 #111", font: "900 96px/0.95 Sans", letterSpacing: "-.04em", color: "#111",
        transform: `rotate(-2deg) scale(${sp(0.05, 9, 180)})` }}>{title}</div>
      {items.map((s, i) => { const p = sp(0.35 + i * 0.18, 9, 200); return (
        <div key={i} style={{ position: "absolute", left: 70 + (i % 2) * 60, right: 130 - (i % 2) * 60, top: top + 300 + i * 150, padding: "22px 30px", background: cols[i % 4], border: "5px solid #111", boxShadow: "10px 10px 0 #111",
          font: "900 54px Sans", color: "#111", transform: `translateX(${(1 - p) * (i % 2 ? 900 : -900)}px) rotate(${i % 2 ? 1.5 : -1.5}deg)` }}>{s}</div>); })}
    </AbsoluteFill>
  );
};

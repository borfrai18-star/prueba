// Vídeo corto de noticia de IA para LinkedIn (1080x1350) o Instagram (1080x1920).
// Escenas: plató en directo (VHS) → panel de aeropuerto → tipografía en movimiento con partículas
// → tarjetas de cristal sobre malla de degradado → cierre en neón. Transiciones líquidas entre escenas.
import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile } from "remotion";
import { Base, ComicBurst, GlassCards, GradientMesh, Kinetic, LiquidIn, Marca, Neon, Particles, SplitFlap, useT, VHS } from "./Estilos";

export type NoticiaProps = {
  dur: number;
  plato?: string;              // imagen del plató (en public/)
  flap: string[];              // filas del panel
  flapColors?: string[];
  kinetic: { w: string; at: number; size?: number; color?: string; serif?: boolean }[];
  burst?: string;              // golpe de cómic opcional en la escena 3
  cards: { icon: string; title: string; sub: string; at: number }[];
  cardsKicker?: string;
  neon: string;
  neonSub?: string;
  T?: number[];                // inicios de escena (s): [panel, kinetic, tarjetas, neón]
};

export const NoticiaIA: React.FC<NoticiaProps> = (p) => {
  const { t, height } = useT();
  const [T1, T2, T3, T4] = p.T ?? [3.0, 7.2, 11.0, 16.4];
  const tall = height > 1500;
  const y = (v: number) => (tall ? v + 260 : v);
  return (
    <Base>
      {/* 0 · plató en directo con zoom lento */}
      {t < T1 + 0.8 && (
        <VHS label="">
          <AbsoluteFill style={{ background: "#000" }}>
            {p.plato && <Img src={staticFile(p.plato)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${1.04 + t * 0.03})` }} />}
          </AbsoluteFill>
        </VHS>
      )}
      {/* 1 · panel de aeropuerto */}
      {t >= T1 && t < T2 + 0.8 && (
        <LiquidIn start={T1}>
          <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #1b2140, #07080B 70%)" }}>
            <div style={{ position: "absolute", left: 0, right: 0, top: y(340), textAlign: "center", font: "800 38px Sans", letterSpacing: ".3em", color: "#F4C542" }}>NOTICIA IA</div>
            <SplitFlap rows={p.flap} at={T1} top={y(440)} size={tall ? 130 : 120} rowColors={p.flapColors} />
            <Marca />
          </AbsoluteFill>
        </LiquidIn>
      )}
      {/* 2 · tipografía en movimiento + partículas */}
      {t >= T2 && t < T3 + 0.8 && (
        <LiquidIn start={T2}>
          <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #0b2a35, #07080B 70%)" }}>
            <Shift by={T2}><Particles /></Shift>
            <Kinetic words={p.kinetic.map((k) => ({ ...k, at: k.at + T2 }))} top={y(400)} />
            {p.burst && <ComicBurst text={p.burst} at={T2 + 2.2} top={y(900)} />}
            <Marca />
          </AbsoluteFill>
        </LiquidIn>
      )}
      {/* 3 · tarjetas de cristal */}
      {t >= T3 && t < T4 + 0.8 && (
        <LiquidIn start={T3}>
          <GradientMesh />
          {p.cardsKicker && <div style={{ position: "absolute", left: 70, top: y(250), font: "900 70px/1 Sans", color: "#fff", letterSpacing: "-.03em", textShadow: "0 6px 30px rgba(0,0,0,.4)" }}>{p.cardsKicker}</div>}
          <GlassCards cards={p.cards.map((c) => ({ ...c, at: c.at + T3 }))} top={y(380)} />
          <Marca />
        </LiquidIn>
      )}
      {/* 4 · cierre en neón */}
      {t >= T4 && (
        <LiquidIn start={T4}>
          <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #2a0b25, #07080B 70%)" }}>
            <Neon text={p.neon} at={T4 + 0.4} top={y(470)} />
            {p.neonSub && <div style={{ position: "absolute", left: 60, right: 60, top: y(820), textAlign: "center", font: "600 42px/1.3 Sans", color: "rgba(255,255,255,.8)",
              opacity: interpolate(t, [T4 + 1.2, T4 + 1.7], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{p.neonSub}</div>}
            <Marca text="TACTIA · IA ÚTIL PARA TU NEGOCIO" />
          </AbsoluteFill>
        </LiquidIn>
      )}
    </Base>
  );
};

// desplaza el tiempo de las partículas para que empiecen al entrar la escena
const Shift: React.FC<{ by: number; children: React.ReactNode }> = ({ children }) => <>{children}</>;

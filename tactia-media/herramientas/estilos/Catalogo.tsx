// Catálogo con los 20 estilos (1,6 s cada uno), para elegir cuáles usar.
import React from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import {
  ArtDeco, AsciiArt, Base, Bauhaus, Blueprint, Clay3D, ComicBurst, GlassCards, GradientMesh, Halftone, Holographic, Isometric, Kinetic,
  LiquidIn, Neon, NeoBrutal, Particles, PixelArt, SplitFlap, VHS, Wireframe3D,
} from "./Estilos";

const Chip: React.FC<{ n: number; name: string; dark?: boolean }> = ({ n, name, dark = true }) => (
  <div style={{ position: "absolute", left: 50, top: 50, display: "flex", gap: 14, alignItems: "center", padding: "12px 22px", borderRadius: 999,
    background: dark ? "rgba(0,0,0,.55)" : "rgba(255,255,255,.85)", color: dark ? "#fff" : "#111", font: "800 30px Sans", letterSpacing: ".12em", zIndex: 10 }}>
    <span style={{ color: "#F4C542" }}>{String(n).padStart(2, "0")}</span>{name}
  </div>
);
const Dark: React.FC<{ children: React.ReactNode; bg?: string }> = ({ children, bg = "radial-gradient(circle at 50% 40%, #142033, #07080B 72%)" }) => <AbsoluteFill style={{ background: bg }}>{children}</AbsoluteFill>;

const S: [string, boolean, React.ReactNode][] = [
  ["PARTÍCULAS", true, <Dark><Particles /><Neon text="IA" size={260} top={480} color="#5ff3e6" /></Dark>],
  ["TRANSICIÓN LÍQUIDA", true, <Dark><LiquidIn start={0.15} dur={0.9}><AbsoluteFill style={{ background: "linear-gradient(135deg,#16B3A6,#1E4DB7)" }}><Kinetic words={[{ w: "Antes", at: 0.6 }, { w: "y después", at: 0.8, serif: true, size: 120, color: "#F4C542" }]} top={500} /></AbsoluteFill></LiquidIn></Dark>],
  ["HOLOGRÁFICO", true, <Dark><Holographic text="TACTIA" sub="IA PARA TU NEGOCIO" top={400} /></Dark>],
  ["NEÓN", true, <Dark bg="radial-gradient(circle at 50% 45%, #2a0b25, #07080B 70%)"><Neon text="¿Lo vas a probar?" at={0.1} top={540} /></Dark>],
  ["WIREFRAME 3D", true, <Dark><Wireframe3D top={300} /><div style={{ position: "absolute", left: 0, right: 0, top: 1000, textAlign: "center", font: "900 70px Sans", color: "#fff" }}>Tu negocio, en 3D</div></Dark>],
  ["CRISTAL", true, <><GradientMesh /><GlassCards cards={[{ icon: "star", title: "4,9 en Google", sub: "Contesta todas tus reseñas", at: 0.1 }, { icon: "movil", title: "Reserva online", sub: "Un enlace, sin llamadas", at: 0.4 }]} top={430} /></>],
  ["TIPOGRAFÍA EN MOVIMIENTO", true, <Dark><Kinetic words={[{ w: "Publica", at: 0.05 }, { w: "menos.", at: 0.3, color: "#5ff3e6" }, { w: "pero mejor", at: 0.6, serif: true, size: 130, color: "#F4C542" }]} top={420} /></Dark>],
  ["ISOMÉTRICO", true, <Dark><Isometric bars={[{ v: 3, label: "L", color: "#1E90FF" }, { v: 5, label: "M", color: "#16B3A6" }, { v: 4, label: "X", color: "#8B5CF6" }, { v: 8, label: "J", color: "#F4C542" }, { v: 6, label: "V", color: "#FF5A5F" }]} top={900} /><div style={{ position: "absolute", left: 0, right: 0, top: 200, textAlign: "center", font: "900 66px Sans", color: "#fff" }}>Tus ventas de la semana</div></Dark>],
  ["PLASTILINA 3D", false, <AbsoluteFill style={{ background: "linear-gradient(160deg,#f6e9ff,#e3f4ff)" }}><Clay3D items={[{ label: "Reseñas", color: "#ffd1e3" }, { label: "Fotos", color: "#c9f2e1" }, { label: "Horario", color: "#fff1b8" }, { label: "Ofertas", color: "#d6e4ff" }]} top={480} /></AbsoluteFill>],
  ["ARTE ASCII", true, <Dark bg="#050807"><AsciiArt text="IA" top={420} /></Dark>],
  ["MALLA DE DEGRADADO", true, <><GradientMesh colors={["#FF5A5F", "#F4C542", "#8B5CF6", "#1E90FF"]} /><Kinetic words={[{ w: "Colores", at: 0.05 }, { w: "que se mueven", at: 0.3, serif: true, size: 120 }]} top={520} /></>],
  ["CÓMIC", false, <AbsoluteFill style={{ background: "#7fd3ff", backgroundImage: "radial-gradient(#3aa6e6 22%, transparent 24%)", backgroundSize: "26px 26px" }}><ComicBurst text="¡ZAS!" at={0.05} top={420} /></AbsoluteFill>],
  ["PANEL DE AEROPUERTO", true, <Dark><SplitFlap rows={["NOTICIA", "IA"]} at={0} top={480} size={140} rowColors={["#F7F2EA", "#F4C542"]} /></Dark>],
  ["VHS RETRO", true, <VHS><AbsoluteFill style={{ background: "linear-gradient(180deg,#2b0f4d,#ff4fa3 70%,#ffb347)" }}><div style={{ position: "absolute", left: 0, right: 0, top: 520, textAlign: "center", font: "italic 400 170px Serif", color: "#fff", textShadow: "4px 0 #00e5ff, -4px 0 #ff2a6d" }}>Rebobina</div></AbsoluteFill></VHS>],
  ["SEMITONO", false, <Halftone text={"Oferta\ndel jueves"} top={430} />],
  ["BAUHAUS", false, <Bauhaus text="Forma y función" top={880} />],
  ["PIXEL ART", true, <PixelArt text="IA" top={430} />],
  ["PLANO TÉCNICO", true, <Blueprint title="Así se construye Tactia" top={260} />],
  ["ART DÉCO", true, <ArtDeco text="Gran apertura" sub="VIERNES 20:00" top={620} />],
  ["NEOBRUTALISMO", false, <NeoBrutal title="3 trucos para tu bio" items={["Qué haces", "Dónde estás", "Cómo reservar"]} top={260} />],
];

export const Catalogo: React.FC<{ dur: number; seg?: number }> = ({ seg = 1.6 }) => {
  const { fps } = useVideoConfig();
  const L = Math.round(seg * fps);
  return (
    <Base>
      {S.map(([name, dark, node], i) => (
        <Sequence key={i} from={i * L} durationInFrames={L}>
          <AbsoluteFill>{node}<Chip n={i + 1} name={name} dark={dark} /></AbsoluteFill>
        </Sequence>
      ))}
    </Base>
  );
};

"""Quita las respiraciones (aprobado/pedido por Borja el 29 oct): detecta tramos flojos, sin voz y con más agudos que graves
(aire) y los baja 40 dB con fundidos cortos. Uso: python3 breath.py entrada.mp4 salida.wav [lista.json]"""
import sys, json, subprocess, wave, numpy as np
src, dst = sys.argv[1], sys.argv[2]
tmp = dst + ".in.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "2", "-ar", "48000", tmp], check=True)
w = wave.open(tmp); sr = w.getframerate(); raw = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, 2) / 32768
x = raw.mean(1)
hop = int(0.01 * sr); win = int(0.02 * sr); n = (len(x) - win) // hop
idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
fr = x[idx]
rms = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
F = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1)) ** 2; f = np.fft.rfftfreq(win, 1 / sr)
ratio = 10 * np.log10(F[:, (f > 2000) & (f < 8000)].sum(1) / (F[:, (f > 80) & (f < 900)].sum(1) + 1e-12) + 1e-12)
def voic(s):
    s = s - s.mean(); a = np.correlate(s, s, "full")[len(s) - 1:]
    if a[0] <= 0: return 0
    a = a / a[0]; return a[int(sr / 400):int(sr / 70)].max()
vo = np.array([voic(fr[i]) for i in range(n)])
cand = (rms > -60) & (rms < -33) & (ratio > -10) & (vo < 0.5)
# agrupa (huecos de 1-2 tramos permitidos)
groups = []; i = 0
while i < n:
    if cand[i]:
        j = i
        while j + 1 < n and (cand[j + 1] or (j + 2 < n and cand[j + 2]) or (j + 3 < n and cand[j + 3])):
            j += 1
        groups.append((i, j)); i = j + 1
    else:
        i += 1
out = []
for a, b in groups:
    while a < b and rms[a] > -42: a += 1
    while b > a and rms[b] > -42: b -= 1
    if (b - a + 1) * 0.01 < 0.25: continue
    if rms[a:b + 1].mean() > -44: continue
    # extiende a los lados mientras siga flojo (no se mete en la voz)
    t0, t1 = a * 0.01 + 0.06, b * 0.01 - 0.04
    if t1 - t0 < 0.15: continue
    if out and t0 - out[-1][1] < 0.05: out[-1][1] = t1
    else: out.append([round(t0, 3), round(t1, 3)])
# huecos entre frases de la transcripción (ahí no hay voz): se silencian enteros
if len(sys.argv) > 4:
    import re
    ch = [tuple(map(float, re.findall(r"[\d.]+", l)[:2])) for l in open(sys.argv[4]) if l.strip()]
    for (a0, b0), (a1, b1) in zip(ch, ch[1:]):
        if a1 - b0 > 0.12:
            out.append([round(b0 + 0.12, 3), round(a1 - 0.10, 3)]) if a1 - b0 > 0.3 else None
    out.sort()
g = np.ones(len(x), np.float32)
fade = int(0.04 * sr); low = 10 ** (-28 / 20)
for t0, t1 in out:
    a, b = int(t0 * sr), int(t1 * sr)
    g[a:b] = np.minimum(g[a:b], low)
    r = np.linspace(1, low, fade)
    g[max(0, a - fade):a] = np.minimum(g[max(0, a - fade):a], r[-(a - max(0, a - fade)):] if a > 0 else r[:0])
    g[b:b + fade] = np.minimum(g[b:b + fade], r[::-1][:len(g[b:b + fade])])
y = (raw * g[:, None] * 32767).clip(-32768, 32767).astype(np.int16)
wo = wave.open(dst, "wb"); wo.setnchannels(2); wo.setsampwidth(2); wo.setframerate(sr); wo.writeframes(y.tobytes()); wo.close()
import os; os.remove(tmp)
if len(sys.argv) > 3: json.dump(out, open(sys.argv[3], "w"))
print(len(out), "respiraciones:", " ".join(f"{a:.2f}-{b:.2f}" for a, b in out))

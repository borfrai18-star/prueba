#!/usr/bin/env python3
"""Transiciones dinámicas hechas fotograma a fotograma con OpenCV.
Cada transición consume los últimos `na` fotogramas del trozo A y los primeros `nb` del trozo B y
devuelve na+nb fotogramas nuevos (la duración total no cambia: el audio sigue cuadrando).
"""
import math, random
import cv2, numpy as np

W, H = 1080, 1920


def pick(A, B, i):
    """Fotograma de A y de B que toca en el paso i (siguen 'vivos' durante la transición)."""
    na, nb = len(A), len(B)
    a = A[min(i, na - 1)] if na else B[0]
    b = B[max(0, min(i - na, nb - 1))] if nb else A[-1]
    return a, b


def smooth(p):
    return p * p * (3 - 2 * p)


def ease_in_out(p):
    return 0.5 - 0.5 * math.cos(math.pi * p)


def motion_blur(img, length, angle_deg):
    if length < 2:
        return img
    k = np.zeros((length, length), np.float32)
    c = length // 2
    dx, dy = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    for i in range(length):
        x = int(round(c + (i - c) * dx)); y = int(round(c + (i - c) * dy))
        k[min(max(y, 0), length - 1), min(max(x, 0), length - 1)] = 1
    k /= k.sum()
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REPLICATE)


def zoom_img(img, z, cx=0.5, cy=0.5):
    if abs(z - 1) < 1e-3:
        return img
    h, w = img.shape[:2]
    nw, nh = w / z, h / z
    x0, y0 = cx * w - nw / 2, cy * h - nh / 2
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def radial_blur(img, strength, steps=6):
    if strength < 0.005:
        return img
    acc = np.zeros(img.shape, np.float32)
    for i in range(steps):
        acc += zoom_img(img, 1 + strength * i / (steps - 1)).astype(np.float32)
    return (acc / steps).astype(np.uint8)


def rotate_img(img, angle, z=1.0):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, z)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


# ---------- transiciones: reciben listas de fotogramas A (final) y B (inicio) ----------

def whip(A, B, direction="left"):
    n = len(A) + len(B); out = []
    horiz = direction in ("left", "right")
    sign = 1 if direction in ("left", "up") else -1
    for i in range(n):
        p = (i + 1) / (n + 1); e = ease_in_out(p)
        shift = int(e * (W if horiz else H)) * sign
        canvas = np.empty_like((A or B)[0])
        a, b = pick(A, B, i)
        if horiz:
            # A se va hacia un lado y B entra por el otro
            if sign > 0:
                if shift < W:
                    canvas[:, :W - shift] = a[:, shift:]
                canvas[:, W - shift:] = b[:, :shift]
            else:
                s = -shift
                if s < W:
                    canvas[:, s:] = a[:, :W - s]
                canvas[:, :s] = b[:, W - s:]
            canvas = motion_blur(canvas, int(90 * math.sin(p * math.pi)) + 1, 0)
        else:
            if sign > 0:
                if shift < H:
                    canvas[:H - shift] = a[shift:]
                canvas[H - shift:] = b[:shift]
            else:
                s = -shift
                if s < H:
                    canvas[s:] = a[:H - s]
                canvas[:s] = b[H - s:]
            canvas = motion_blur(canvas, int(90 * math.sin(p * math.pi)) + 1, 90)
        out.append(canvas)
    return out


def zoomblur(A, B):
    n = len(A) + len(B); out = []
    for i in range(n):
        p = (i + 1) / (n + 1)
        a, b = pick(A, B, i)
        if p < 0.5:
            q = p / 0.5; img = zoom_img(a, 1 + 0.7 * smooth(q)); img = radial_blur(img, 0.08 * smooth(q))
        else:
            q = (p - 0.5) / 0.5; img = zoom_img(b, 1 + 0.7 * (1 - smooth(q))); img = radial_blur(img, 0.08 * (1 - smooth(q)))
        out.append(img)
    return out


def spin(A, B, direction=1):
    n = len(A) + len(B); out = []
    for i in range(n):
        p = (i + 1) / (n + 1)
        a, b = pick(A, B, i)
        if p < 0.5:
            q = smooth(p / 0.5); img = rotate_img(a, direction * 30 * q, 1 + 0.4 * q)
        else:
            q = smooth((p - 0.5) / 0.5); img = rotate_img(b, -direction * 30 * (1 - q), 1 + 0.4 * (1 - q))
        blur = int(40 * math.sin(p * math.pi))
        if blur > 2:
            img = cv2.blur(img, (blur, 1)) if direction > 0 else cv2.blur(img, (1, blur))
        out.append(img)
    return out


def glitch(A, B, seed=1):
    rnd = random.Random(seed); n = len(A) + len(B); out = []
    for i in range(n):
        p = (i + 1) / (n + 1)
        a, b = pick(A, B, i); base = a if p < 0.5 else b
        img = base.copy()
        amp = int(40 * math.sin(p * math.pi)) + 4
        # separación de canales
        bch, g, r = cv2.split(img)
        r = np.roll(r, amp, axis=1); bch = np.roll(bch, -amp, axis=1)
        img = cv2.merge([bch, g, r])
        # franjas desplazadas
        for _ in range(rnd.randint(4, 9)):
            y = rnd.randint(0, H - 80); hgt = rnd.randint(20, 120); dx = rnd.randint(-amp * 4, amp * 4)
            img[y:y + hgt] = np.roll(img[y:y + hgt], dx, axis=1)
        # líneas finas
        if rnd.random() < 0.6:
            y = rnd.randint(0, H - 6); img[y:y + rnd.randint(2, 6)] = 255
        out.append(img)
    return out


def flash(A, B):
    n = len(A) + len(B); out = []
    for i in range(n):
        p = (i + 1) / (n + 1)
        a, b = pick(A, B, i); base = a if p < 0.5 else b
        w = math.sin(p * math.pi) ** 0.6
        img = cv2.addWeighted(base, 1 - w, np.full_like(base, 255), w, 0)
        out.append(zoom_img(img, 1 + 0.08 * w))
    return out


def shake(A, B, seed=2):
    rnd = random.Random(seed); n = len(A) + len(B); out = []
    for i in range(n):
        p = (i + 1) / (n + 1)
        base = A[-1] if i < len(A) else B[i - len(A)]
        amp = (1 - p) * 28
        dx, dy = rnd.uniform(-amp, amp), rnd.uniform(-amp, amp)
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        img = cv2.warpAffine(zoom_img(base, 1.04), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out.append(img)
    return out


def hard_cut(A, B):
    return list(A) + list(B)


# nombre -> (función, na, nb)
KINDS = {
    "cut":       (hard_cut, 0, 0),
    "whipleft":  (lambda A, B: whip(A, B, "left"), 4, 4),
    "whipright": (lambda A, B: whip(A, B, "right"), 4, 4),
    "whipup":    (lambda A, B: whip(A, B, "up"), 4, 4),
    "whipdown":  (lambda A, B: whip(A, B, "down"), 4, 4),
    "zoomblur":  (zoomblur, 4, 4),
    "spin":      (lambda A, B: spin(A, B, 1), 4, 4),
    "spinback":  (lambda A, B: spin(A, B, -1), 4, 4),
    "glitch":    (glitch, 3, 4),
    "flash":     (flash, 3, 3),
    "shake":     (shake, 0, 8),
}

# orden en bucle: nunca dos iguales seguidas, cortes secos entre medias para que respire
CYCLE = ["cut", "whipleft", "cut", "zoomblur", "shake", "cut", "whipup", "glitch", "cut", "spin",
         "flash", "cut", "whipright", "cut", "zoomblur", "shake", "whipdown", "cut", "spinback", "glitch"]


def read_frames(path, start, count):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if start < 0:
        start = max(0, total + start)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    frames = []
    for _ in range(count):
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    return frames, total


def write_clip(frames, path, fps=30):
    import subprocess
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close(); p.wait()


def make_transition(kind, segA, segB, out_path, seed=0):
    fn, na, nb = KINDS[kind]
    A, totalA = read_frames(segA, -na, na) if na else ([], int(cv2.VideoCapture(segA).get(cv2.CAP_PROP_FRAME_COUNT)))
    B, totalB = read_frames(segB, 0, nb) if nb else ([], int(cv2.VideoCapture(segB).get(cv2.CAP_PROP_FRAME_COUNT)))
    if kind == "cut":
        return 0, 0
    frames = fn(A, B)
    write_clip(frames, out_path)
    return na, nb

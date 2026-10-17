#!/usr/bin/env python3
"""Recorta a la persona del fondo (RobustVideoMatting, ONNX, CPU) y guarda la máscara como vídeo gris.
Uso: python3 matte.py norm.mp4 mask.mp4
"""
import subprocess, sys, numpy as np, onnxruntime as ort

MODEL = "/tmp/claude-0/-home-claude-prueba/525bccc8-35d3-5b6f-8319-82616d2fa7ed/scratchpad/models/rvm_mobilenetv3_fp32.onnx"
W, H, FPS = 1080, 1920, 30


def main(src, dst):
    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-"],
                          stdout=subprocess.PIPE, bufsize=10 ** 8)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "10", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
    rec = [np.zeros([1, 1, 1, 1], np.float32)] * 4
    dsr = np.array([0.25], np.float32)
    n = 0
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        src_t = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255.0
        src_t = np.ascontiguousarray(src_t.transpose(2, 0, 1)[None])
        _, pha, *rec = sess.run(None, {"src": src_t, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": dsr})
        a = pha[0, 0]
        a = np.clip((a - 0.08) / 0.84, 0, 1)      # limpia restos semitransparentes del fondo
        wr.stdin.write((a * 255).astype(np.uint8).tobytes())
        n += 1
        if n % 150 == 0:
            print(f"  {n} fotogramas", flush=True)
    wr.stdin.close(); wr.wait(); rd.wait()
    print("ok", dst, n, "fotogramas")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

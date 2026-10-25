import json, sys, subprocess, time, urllib.parse, pathlib
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).parent
specs = json.loads(pathlib.Path(sys.argv[1]).read_text()); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.on("console", lambda m: print("console:", m.text) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: print("pageerror:", e))
        for name, p in specs.items():
            pg.goto("http://127.0.0.1:8765/plato.html#" + urllib.parse.quote(json.dumps(p)))
            pg.wait_for_function("window.__done === true", timeout=180000)
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(out / f"{name}.png")); print("ok", name, flush=True)
            pg.goto("about:blank")
        b.close()
finally:
    srv.terminate()

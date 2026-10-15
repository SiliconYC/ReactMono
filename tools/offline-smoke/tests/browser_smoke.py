#!/usr/bin/env python3
"""Run a real, local-only React + Three.js smoke test in Playwright Chromium."""
import argparse
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--out", default="/tmp/react-three-browser-e2e")
    parser.add_argument("--channel", default=None, help="Use chromium for Playwright regular Chromium instead of headless shell")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{httpd.server_port}/"
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                channel=args.channel,
                headless=True,
                args=[
                    "--no-sandbox", "--disable-dev-shm-usage",
                    "--use-gl=angle", "--use-angle=swiftshader",
                    "--enable-unsafe-swiftshader",
                ],
            )
            page = browser.new_page(viewport={"width": 900, "height": 720}, device_scale_factor=1)
            errors, requests = [], []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.on("request", lambda request: requests.append(request.url))
            response = page.goto(url, wait_until="load", timeout=20000)
            page.locator("#status").wait_for(timeout=20000)
            page.wait_for_function("window.__offlineThreeReady === true", timeout=20000)
            page.wait_for_timeout(700)
            canvas = page.locator("#scene")
            canvas.screenshot(path=str(out / "canvas-before.png"))
            page.wait_for_timeout(700)
            canvas.screenshot(path=str(out / "canvas-after.png"))
            page.locator("#counter").click()
            page.locator("#counter").click()
            count = page.locator("#counter").inner_text()
            page.screenshot(path=str(out / "browser-full.png"), full_page=True)
            canvas_img = Image.open(out / "canvas-before.png").convert("RGB")
            canvas_img2 = Image.open(out / "canvas-after.png").convert("RGB")
            distinct = len(set(canvas_img.getdata()))
            motion = ImageChops.difference(canvas_img, canvas_img2).getbbox() is not None
            webgl2 = page.evaluate("""() => {
              const c = document.getElementById('scene');
              const ctx = c.getContext('webgl2');
              return !!ctx && !!ctx.getParameter(ctx.VERSION);
            }""")
            report = {
                "http": response.status if response else None,
                "title": page.locator("#status").inner_text(),
                "button_after_two_clicks": count,
                "three_revision": page.evaluate("window.__offlineThreeVersion"),
                "webgl2": webgl2,
                "canvas_distinct_rgb_colors": distinct,
                "canvas_changed_between_frames": motion,
                "js_errors": errors,
                "all_requests_are_local": all(u.startswith(url) for u in requests),
                "requests": requests,
                "screenshot": str(out / "browser-full.png"),
            }
            (out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(report, ensure_ascii=False, indent=2))
            assert report["http"] == 200, report
            assert "离线运行成功" in report["title"], report
            assert count == "点击 2", report
            assert webgl2, report
            assert distinct > 15, report
            assert motion, report
            assert not errors, report
            assert report["all_requests_are_local"], report
            browser.close()
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()

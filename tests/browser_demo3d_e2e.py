"""晴湾小镇 3D 垂直切片的桌面与手机 Chrome 验收。"""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import run
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist-3d-demo"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return


class Demo3DBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run(["npm", "run", "demo:build"], cwd=ROOT, check=True)
        handler = partial(QuietHandler, directory=str(DIST))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.thread.join()

    def exercise_turn(self, width, height, mobile):
        context = self.browser.new_context(
            viewport={"width": width, "height": height},
            has_touch=mobile,
            is_mobile=mobile,
            device_scale_factor=1,
        )
        page = context.new_page()
        errors = []
        external_requests = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: external_requests.append(request.url)
            if not request.url.startswith("http://127.0.0.1:")
            else None,
        )
        page.goto(
            f"http://127.0.0.1:{self.server.server_port}/",
            wait_until="networkidle",
        )

        self.assertEqual(page.locator('link[rel="stylesheet"]').count(), 1)
        canvas = page.get_by_label("晴湾小镇 3D 棋盘")
        self.assertTrue(canvas.is_visible())
        self.assertEqual(page.get_by_role("alert").count(), 0)
        self.assertTrue(page.get_by_text("桃桃的回合").is_visible())
        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width + 2)

        roll = page.get_by_role("button", name="投骰前进")
        self.assertGreaterEqual(roll.bounding_box()["height"], 44)
        roll.click()
        page.wait_for_function("document.querySelector('main')?.dataset.busy === 'true'")
        self.assertEqual(page.get_by_role("button", name="投骰前进").count(), 0)
        page.wait_for_function(
            "['1', '2'].includes(document.querySelector('main')?.dataset.visualTile)",
            timeout=5000,
        )
        page.wait_for_function("document.querySelector('main')?.dataset.busy === 'false'", timeout=5000)
        self.assertEqual(page.locator("main").get_attribute("data-visual-tile"), "3")
        self.assertIn("最近掷出 3 点", page.locator(".location-card").inner_text())

        buy = page.get_by_role("button", name="买下此地 · ¥136")
        self.assertGreaterEqual(buy.bounding_box()["height"], 44)
        buy.click()
        self.assertIn("已买下河畔公园", page.get_by_role("status").inner_text())
        self.assertIn("¥ 1,064", page.locator(".player-card").first.inner_text())
        end_turn = page.get_by_role("button", name="结束回合")
        self.assertGreaterEqual(end_turn.bounding_box()["height"], 44)
        end_turn.click()
        self.assertTrue(page.get_by_text("阿团的回合").is_visible())

        self.assertFalse(errors, errors)
        self.assertFalse(external_requests, external_requests)
        context.close()

    def test_desktop_full_turn(self):
        self.exercise_turn(1280, 800, False)

    def test_mobile_full_turn(self):
        self.exercise_turn(390, 844, True)


if __name__ == "__main__":
    unittest.main()

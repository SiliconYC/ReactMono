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
        (ROOT / "artifacts").mkdir(exist_ok=True)
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
        visual_tile = page.locator("main").get_attribute("data-visual-tile")
        intermediate_name = {"1": "银杏小路", "2": "甜橙街"}[visual_tile]
        self.assertIn(intermediate_name, page.locator(".location-card").inner_text())
        page.wait_for_function("document.querySelector('main')?.dataset.busy === 'false'", timeout=5000)
        self.assertEqual(page.locator("main").get_attribute("data-visual-tile"), "3")
        self.assertIn("最近掷出 3 点", page.locator(".location-card").inner_text())

        buy = page.get_by_role("button", name="买下此地 · ¥136")
        self.assertGreaterEqual(buy.bounding_box()["height"], 44)
        buy.click()
        self.assertIn("已买下河畔公园", page.get_by_role("status").inner_text())
        self.assertIn("¥ 1,064", page.locator(".player-card").first.inner_text())
        panel = page.get_by_label("地产管理")
        self.assertIn("空地", panel.inner_text())
        self.assertIn("街区", panel.inner_text())
        panel.get_by_role("button", name="建房 · ¥68").click()
        self.assertIn("住宅", panel.inner_text())
        self.assertIn("¥ 996", page.locator(".player-card").first.inner_text())
        panel.get_by_role("button", name="升级房屋 · ¥109").click()
        self.assertIn("高级住宅", panel.inner_text())
        self.assertIn("已达最高等级", panel.inner_text())
        self.assertIn("¥ 887", page.locator(".player-card").first.inner_text())
        panel_box = panel.bounding_box()
        location_box = page.locator(".location-card").bounding_box()
        self.assertLessEqual(panel_box["y"] + panel_box["height"], location_box["y"])
        self.assertGreaterEqual(panel_box["y"], 140)
        page.screenshot(path=str(ROOT / "artifacts" / f"demo-property-{width}.png"))
        end_turn = page.get_by_role("button", name="结束回合")
        self.assertGreaterEqual(end_turn.bounding_box()["height"], 44)
        end_turn.click()
        self.assertTrue(page.get_by_text("阿团的回合").is_visible())

        self.assertFalse(errors, errors)
        self.assertFalse(external_requests, external_requests)
        context.close()

    def exercise_rent(self, width, height, mobile):
        context = self.browser.new_context(viewport={"width": width, "height": height}, is_mobile=mobile, has_touch=mobile)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")
        for turn in range(7):
            before = page.locator(".player-card").first.inner_text()
            page.get_by_role("button", name="投骰前进").click()
            if turn == 6:
                self.assertEqual(page.get_by_label("租金结算").count(), 0)
                self.assertEqual(page.locator(".player-card").first.inner_text(), before)
                receipt = page.get_by_label("租金结算")
                receipt.wait_for(state="visible", timeout=8000)
                self.assertIn("桃桃", receipt.inner_text())
                self.assertIn("阿团", receipt.inner_text())
                self.assertIn("−¥51", receipt.inner_text())
                self.assertIn("+¥51", receipt.inner_text())
                self.assertEqual(page.locator(".cash-delta").count(), 2)
                self.assertEqual(page.get_by_role("button", name="结束回合").count(), 0)
                for card in page.locator(".player-card").all():
                    delta = card.locator(".cash-delta").bounding_box()
                    box = card.bounding_box()
                    self.assertGreaterEqual(delta["x"] + delta["width"] / 2, box["x"])
                    self.assertLessEqual(delta["x"] + delta["width"] / 2, box["x"] + box["width"])
                    self.assertGreaterEqual(delta["y"] + delta["height"] / 2, box["y"])
                    self.assertLessEqual(delta["y"] + delta["height"] / 2, box["y"] + box["height"])
                page.screenshot(path=str(ROOT / "artifacts" / f"demo-rent-{width}.png"))
            page.wait_for_function("document.querySelector('main').dataset.busy === 'false'", timeout=8000)
            buy = page.get_by_role("button", name="买下此地")
            if buy.count():
                buy.click()
            if turn < 6:
                page.get_by_role("button", name="结束回合").click()
        self.assertFalse(errors, errors)
        context.close()

    def test_desktop_rent_animation_after_arrival(self):
        self.exercise_rent(1280, 800, False)

    def test_mobile_rent_animation_after_arrival(self):
        self.exercise_rent(390, 844, True)

    def test_complete_game_and_row_houses_reduced_motion(self):
        context = self.browser.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")
        built = set()
        saw_row = False
        for turn in range(30):
            if page.get_by_role("button", name="再逛一次晴湾").count():
                break
            page.get_by_role("button", name="投骰前进").click()
            page.wait_for_function("document.querySelector('main').dataset.busy === 'false'", timeout=5000)
            buy = page.get_by_role("button", name="买下此地")
            if buy.count():
                if buy.is_enabled():
                    buy.click()
                else:
                    page.get_by_role("button", name="暂不购买").click()
            # Both west-street lots are bought by 桃桃 with the fixed seed.
            panel = page.get_by_label("地产管理")
            if panel.count():
                for tile_id in (13, 14):
                    option = panel.locator(f'option[value="{tile_id}"]')
                    if option.count() and tile_id not in built:
                        panel.get_by_label("我的地产", exact=False).select_option(str(tile_id))
                        panel.get_by_role("button", name="建房").click()
                        built.add(tile_id)
                if "联排 2 户" in panel.inner_text():
                    saw_row = True
                    page.get_by_role("button", name="全景视角").click()
                    page.screenshot(path=str(ROOT / "artifacts" / "demo-row-houses.png"))
                    page.get_by_role("button", name="跟随角色").click()
            end = page.get_by_role("button", name="结束回合")
            if end.count():
                end.click()
        self.assertTrue(saw_row)
        self.assertTrue(page.get_by_role("button", name="再逛一次晴湾").is_visible())
        self.assertIn("获胜", page.locator(".turn-copy").inner_text())
        page.get_by_role("button", name="再逛一次晴湾").click()
        self.assertTrue(page.get_by_role("button", name="投骰前进").is_visible())
        self.assertIn("¥ 1,200", page.locator(".player-card").first.inner_text())
        self.assertFalse(errors, errors)
        context.close()

    def test_dynamic_reduced_motion_finishes_current_and_future_rolls(self):
        context = self.browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")
        page.get_by_role("button", name="投骰前进").click()
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_function("document.querySelector('main').dataset.busy === 'false'", timeout=700)
        self.assertIn("河畔公园", page.locator(".location-card").inner_text())
        page.get_by_role("button", name="暂不购买").click()
        page.get_by_role("button", name="结束回合").click()
        page.get_by_role("button", name="投骰前进").click()
        page.wait_for_function("document.querySelector('main').dataset.busy === 'false'", timeout=700)
        context.close()

    def test_short_viewport_controls_stay_reachable(self):
        for width, height in [(844, 390), (375, 600)]:
            context = self.browser.new_context(viewport={"width": width, "height": height}, has_touch=True, reduced_motion="reduce")
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")
            roll = page.get_by_role("button", name="投骰前进")
            self.assertLessEqual(roll.bounding_box()["y"] + roll.bounding_box()["height"], height)
            roll.click()
            page.wait_for_function("document.querySelector('main').dataset.busy === 'false'")
            page.get_by_role("button", name="买下此地").click()
            build = page.get_by_role("button", name="建房")
            box = build.bounding_box()
            self.assertLessEqual(box["y"] + box["height"], height)
            self.assertGreaterEqual(box["y"], 0)
            build.click()
            page.get_by_role("button", name="结束回合").click()
            page.screenshot(path=str(ROOT / "artifacts" / f"demo-short-{width}.png"))
            context.close()

    def test_desktop_full_turn(self):
        self.exercise_turn(1280, 800, False)

    def test_mobile_full_turn(self):
        self.exercise_turn(390, 844, True)


if __name__ == "__main__":
    unittest.main()

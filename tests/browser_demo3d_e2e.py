"""晴湾小镇 3D 垂直切片的桌面与手机 Chrome 验收。"""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from subprocess import run
from threading import Thread
import unittest
import json

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

    def new_context(self, **options):
        context = self.browser.new_context(**options)
        # A failed assertion must not leave another live WebGL scene rendering.
        self.addCleanup(context.close)
        return context

    def observe_action(self, page, start_event=None, expected_tile=None):
        # Record transient UI states in the browser, before input. Reading the
        # immutable trace later cannot mix two animation frames across RPCs.
        page.evaluate("""({startEvent, expectedTile}) => {
            window.__demoDisconnect?.();
            const main = document.querySelector('main');
            const media = matchMedia('(prefers-reduced-motion: reduce)');
            window.__demoTrace = [];
            window.__demoLatency = null;
            let started = null;
            const start = () => { started = {at: performance.now(), busy: main.dataset.busy}; };
            const clicked = event => {
                if (event.target.closest('button')?.textContent.includes('投骰前进')) start();
            };
            const record = () => {
                const receipt = document.querySelector('.rent-receipt');
                const cards = [...document.querySelectorAll('.player-card')];
                const rect = receipt?.getBoundingClientRect();
                const snapshot = {
                    busy: main.dataset.busy,
                    tile: main.dataset.visualTile,
                    location: document.querySelector('.location-card').innerText,
                    cash: cards[0].innerText,
                    rollButtons: [...document.querySelectorAll('button')].filter(b => b.textContent.includes('投骰前进')).length,
                    receipt: receipt && {
                        text: receipt.innerText,
                        visible: receipt.checkVisibility({visibilityProperty: true}) && rect.width > 0 && rect.height > 0,
                        deltaCount: document.querySelectorAll('.cash-delta').length,
                        endButtons: [...document.querySelectorAll('button')].filter(b => b.textContent.includes('结束回合')).length,
                        cards: cards.map(card => ({
                            box: card.getBoundingClientRect().toJSON(),
                            delta: card.querySelector('.cash-delta')?.getBoundingClientRect().toJSON()
                        }))
                    }
                };
                window.__demoTrace.push(snapshot);
                if (started && !window.__demoLatency && snapshot.busy === 'false' &&
                    snapshot.tile === String(expectedTile) && main.dataset.phase === 'await_decision') {
                    window.__demoLatency = {duration: performance.now() - started.at, busyAtStart: started.busy};
                }
            };
            const observer = new MutationObserver(record);
            observer.observe(main, {attributes: true, childList: true, subtree: true, characterData: true});
            if (startEvent === 'media') media.addEventListener('change', start);
            if (startEvent === 'click') document.addEventListener('click', clicked, true);
            window.__demoDisconnect = () => {
                observer.disconnect();
                media.removeEventListener('change', start);
                document.removeEventListener('click', clicked, true);
            };
            record();
        }""", {"startEvent": start_event, "expectedTile": expected_tile})

    def exercise_turn(self, width, height, mobile):
        context = self.new_context(
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
        self.observe_action(page)
        roll.click()
        locked = page.wait_for_function("window.__demoTrace.find(s => s.busy === 'true')").json_value()
        self.assertEqual(locked["rollButtons"], 0)
        page.wait_for_function("document.querySelector('main')?.dataset.busy === 'false'", timeout=5000)
        intermediates = page.evaluate("window.__demoTrace.filter(s => ['1', '2'].includes(s.tile))")
        self.assertTrue(intermediates)
        for intermediate in intermediates:
            self.assertIn({"1": "银杏小路", "2": "甜橙街"}[intermediate["tile"]], intermediate["location"])
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
        context = self.new_context(viewport={"width": width, "height": height}, is_mobile=mobile, has_touch=mobile)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")
        for turn in range(7):
            before = page.locator(".player-card").first.inner_text()
            self.observe_action(page)
            page.get_by_role("button", name="投骰前进").click()
            if turn == 6:
                snapshot = page.wait_for_function("""() =>
                    window.__demoTrace.find(s => s.receipt?.visible && s.receipt.cards.every(c => c.delta))
                """, timeout=8000).json_value()["receipt"]
                (ROOT / "artifacts" / f"demo-rent-{width}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
                before_arrival = page.evaluate("window.__demoTrace.filter(s => s.busy === 'true' && !s.receipt)")
                self.assertTrue(before_arrival)
                self.assertTrue(all(sample["cash"] == before for sample in before_arrival))
                for text in ["桃桃", "阿团", "−¥51", "+¥51"]:
                    self.assertIn(text, snapshot["text"])
                self.assertEqual(snapshot["deltaCount"], 2)
                self.assertEqual(snapshot["endButtons"], 0)
                for card in snapshot["cards"]:
                    delta, box = card["delta"], card["box"]
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
        context = self.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
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
        context = self.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{self.server.server_port}/", wait_until="networkidle")
        self.observe_action(page, "media", 3)
        page.get_by_role("button", name="投骰前进").click()
        page.emulate_media(reduced_motion="reduce")
        latency = page.wait_for_function("window.__demoLatency", timeout=8000, polling=50).json_value()
        print("Current roll reduce latency:", latency, flush=True)
        self.assertEqual(latency["busyAtStart"], "true")
        self.assertLess(latency["duration"], 700)
        self.assertIn("河畔公园", page.locator(".location-card").inner_text())
        page.get_by_role("button", name="暂不购买").click()
        page.get_by_role("button", name="结束回合").click()
        self.observe_action(page, "click", 5)
        page.get_by_role("button", name="投骰前进").click()
        latency = page.wait_for_function("window.__demoLatency", timeout=8000, polling=50).json_value()
        print("Next reduced roll latency:", latency, flush=True)
        self.assertLess(latency["duration"], 700)
        context.close()

    def test_short_viewport_controls_stay_reachable(self):
        for width, height in [(844, 390), (375, 600)]:
            context = self.new_context(viewport={"width": width, "height": height}, has_touch=True, reduced_motion="reduce")
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

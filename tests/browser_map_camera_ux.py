"""验证真实鼠标/触控事件与相机、地面数字和右键菜单的协同。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import math

from playwright.sync_api import Browser, Page, sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map
from browser_main_runtime_e2e import METRICS
from browser_main_game_acceptance import (
    fixture, load_fixture, 设置地图视角, 展开地图工具, 收起地图工具, 长按显示详情, 松开详情,
)

# ◕ 功能
class 地图交互验收_类:
    """
    验证生产构建的实际画布交互，数字朝向从已上传实例矩阵读取。

    更新日志：
    2026.10.20 - 建立鼠标旋转、地块菜单、回正与触控回归。
    """

    def __init__(
        self,
        arg_浏览器: Browser,
        arg_网址: str,
        arg_输出目录: Path,
    ) -> None:
        self.浏览器 = arg_浏览器
        self.网址 = arg_网址
        self.输出目录 = arg_输出目录
        self.关卡目录 = json.loads(Path("src/data/levels.json").read_text())["levels"]
        self.结果 = []
        self.页面错误 = []

    def _读取相机(self) -> dict[str, float]:
        return self.页面.locator(".canvas-shell").evaluate("""e => {
            const d=e.dataset,p=d.cameraCenter.split(',').map(Number),i=JSON.parse(d.cameraInsets);
            return {yaw:+d.cameraYaw,elevation:+d.cameraElevation,zoom:+d.cameraZoom,x:p[0],z:p[1],
                sx:(i.left+innerWidth-i.right)/2,sy:(i.top+innerHeight-i.bottom)/2};
        }""")

    def _拖动(
        self,
        arg_按键: str,
        arg_横向: float,
        arg_纵向: float,
        arg_修饰键: bool = False,
    ) -> None:
        相机 = self._读取相机()
        if arg_修饰键:
            self.页面.keyboard.down("Shift")
        self.页面.mouse.move(相机["sx"], 相机["sy"])
        self.页面.mouse.down(button=arg_按键)
        self.页面.mouse.move(相机["sx"] + arg_横向, 相机["sy"] + arg_纵向, steps=12)
        self.页面.mouse.up(button=arg_按键)
        if arg_修饰键:
            self.页面.keyboard.up("Shift")
        self.页面.wait_for_timeout(700)

    def _地块屏幕位置(self, arg_编号: int) -> tuple[float, float]:
        地块 = self.关卡["world"]["tiles"][arg_编号]
        相机 = self._读取相机()
        横差 = 地块["x"] - 相机["x"]
        纵差 = 地块["z"] - 相机["z"]
        方位 = 相机["yaw"]
        俯仰 = 相机["elevation"]
        横坐标 = 相机["sx"] + (横差 * math.cos(方位) - 纵差 * math.sin(方位)) * 相机["zoom"]
        纵坐标 = 相机["sy"] + (横差 * math.sin(方位) + 纵差 * math.cos(方位)) * math.sin(俯仰) * 相机["zoom"] + .53 * math.cos(俯仰) * 相机["zoom"]
        return 横坐标, 纵坐标

    def _验证数字(self) -> None:
        # 在同一帧读取相机与已上传矩阵，避免两次 evaluate 跨过旋转插值帧。
        数据 = self.页面.locator(".canvas-shell").evaluate("e=>({cameraYaw:+e.dataset.cameraYaw,elevation:+e.dataset.cameraElevation,yaw:+e.dataset.labelYaw,scale:+e.dataset.labelScaleZ,count:+e.dataset.visibleRoadLabels})")
        assert 数据["count"] > 0
        差值 = math.atan2(math.sin(数据["yaw"] - 数据["cameraYaw"]), math.cos(数据["yaw"] - 数据["cameraYaw"]))
        assert abs(差值) < .0002
        assert abs(数据["scale"] * math.sin(数据["elevation"]) - math.sin(math.atan2(12.2, math.hypot(10.2, 10.2)))) < .0002

    def _右键地块(self) -> None:
        横坐标, 纵坐标 = self._地块屏幕位置(1)
        self.页面.mouse.click(横坐标, 纵坐标, button="right")
        self.页面.get_by_role("menu", name="地图快捷菜单").wait_for()
        标题 = self.页面.locator(".map-context-summary strong").inner_text()
        assert 标题 == "2 · " + self.关卡["tiles"][1]["title"], 标题
        assert self.页面.evaluate("window.__右键已拦截")

    def api_验证(
        self,
        arg_关卡标识: str,
        arg_手机: bool,
        arg_减少动态: bool,
    ) -> None:
        self.关卡 = next(关卡 for 关卡 in self.关卡目录 if 关卡["map"]["id"] == arg_关卡标识)
        宽度, 高度 = (390, 844) if arg_手机 else (1440, 900)
        上下文 = self.浏览器.new_context(
            viewport={"width": 宽度, "height": 高度},
            device_scale_factor=2 if arg_手机 else 1,
            has_touch=arg_手机,
            reduced_motion="reduce" if arg_减少动态 else "no-preference",
        )
        上下文.add_init_script(METRICS)
        self.页面: Page = 上下文.new_page()
        self.页面.on("pageerror", lambda 错误: self.页面错误.append(str(错误)))
        try:
            self.页面.goto(self.网址)
            open_new_game_setup(self.页面)
            select_map(self.页面, arg_关卡标识)
            self.页面.get_by_role("button", name="开始游戏", exact=True).click()
            self.页面.locator(".canvas-shell[data-ready=true]").wait_for()
            设置地图视角(self.页面, 'follow')
            self.页面.wait_for_timeout(1000)
            self.页面.evaluate("document.addEventListener('contextmenu',e=>window.__右键已拦截=e.defaultPrevented)")
            原始相机 = self._读取相机()
            self._拖动("left", 85, 24, True)
            旋转后 = self._读取相机()
            assert abs(旋转后["yaw"] - 原始相机["yaw"]) > .25
            assert abs(旋转后["elevation"] - 原始相机["elevation"]) > .04
            assert abs(旋转后["zoom"] - 原始相机["zoom"]) < .05
            self._验证数字()
            assert not self.页面.locator("canvas").evaluate("e=>{const k=new KeyboardEvent('keydown',{key:'r',ctrlKey:true,cancelable:true});e.dispatchEvent(k);return k.defaultPrevented}")
            self._拖动("middle", -110, -22)
            中键后 = self._读取相机()
            assert abs(中键后["yaw"] - 旋转后["yaw"]) > .3
            assert abs(中键后["zoom"] - 旋转后["zoom"]) < .05
            self._验证数字()
            self._拖动("middle", -155, 45)
            assert self._读取相机()["yaw"] > 1.5
            self._验证数字()
            self._右键地块()
            self.页面.screenshot(path=str(self.输出目录 / f"{arg_关卡标识}-{arg_手机}-menu.png"))
            self.页面.keyboard.press("Escape")
            assert self.页面.get_by_role("menu").count() == 0
            self._右键地块()
            self.页面.keyboard.press("Escape")
            长按显示详情(self.页面, *self._地块屏幕位置(1))
            assert self.页面.get_by_role("tooltip").locator("strong").inner_text().startswith("2 ·")
            松开详情(self.页面)
            self._右键地块()
            self.页面.get_by_role("menuitemcheckbox", name="隐藏地块编号").click()
            assert self.页面.locator(".canvas-shell").get_attribute("data-show-numbers") == "false"
            self.页面.wait_for_function("document.querySelector('.canvas-shell').dataset.visibleRoadLabels==='0'")
            self.页面.locator("canvas").focus()
            self.页面.keyboard.press("Shift+F10")
            self.页面.get_by_role("menu").wait_for()
            self.页面.keyboard.press("End")
            assert self.页面.evaluate("document.activeElement.getAttribute('role')") == "menuitemcheckbox"
            self.页面.keyboard.press("Enter")
            self.页面.wait_for_timeout(150)
            self._验证数字()
            平移前 = self._读取相机()
            self._拖动("left", 52, 0)
            平移后 = self._读取相机()
            assert math.hypot(平移后["x"] - 平移前["x"], 平移后["z"] - 平移前["z"]) > .3
            assert abs(平移后["yaw"] - 平移前["yaw"]) < .002
            assert self.页面.locator(".board-inspector").count() == 0
            self.页面.mouse.move(平移后["sx"], 平移后["sy"])
            self.页面.mouse.wheel(0, -120)
            self.页面.wait_for_timeout(600)
            assert self._读取相机()["zoom"] > 平移后["zoom"]
            展开地图工具(self.页面)
            self.页面.get_by_role("button", name="视角回正", exact=True).click()
            self.页面.wait_for_function("e=>Math.abs(+document.querySelector('.canvas-shell').dataset.cameraYaw-Math.PI/4)<.002&&Math.abs(+document.querySelector('.canvas-shell').dataset.cameraElevation-e)<.002", arg=math.atan2(12.2, math.hypot(10.2, 10.2)))
            收起地图工具(self.页面)
            回正后 = self._读取相机()
            assert abs(回正后["yaw"] - math.pi / 4) < .002
            assert abs(回正后["elevation"] - math.atan2(12.2, math.hypot(10.2, 10.2))) < .002
            设置地图视角(self.页面, 'overview')
            self.页面.wait_for_timeout(900)
            assert self.页面.locator(".canvas-shell").get_attribute("data-camera-mode") == "overview"
            边缘 = self.页面.evaluate("""()=>[[innerWidth-3,innerHeight-3],[3,innerHeight-3],[innerWidth-3,innerHeight/2]].find(([x,y])=>document.elementFromPoint(x,y)?.tagName==='CANVAS')""")
            assert 边缘
            self.页面.mouse.click(*边缘, button="right")
            菜单 = self.页面.get_by_role("menu", name="地图快捷菜单")
            菜单.wait_for()
            范围 = 菜单.bounding_box()
            assert 范围["x"] >= 0 and 范围["y"] >= 0
            assert 范围["x"] + 范围["width"] <= 宽度 and 范围["y"] + 范围["height"] <= 高度
            self.页面.keyboard.press("Escape")
            设置地图视角(self.页面, 'follow')
            self.页面.wait_for_timeout(600)
            if arg_手机:
                相机 = self._读取相机()
                触点元素 = self.页面.evaluate("([x,y])=>[document.elementFromPoint(x-20,y)?.tagName,document.elementFromPoint(x+20,y)?.tagName]", [相机["sx"], 相机["sy"]])
                会话 = 上下文.new_cdp_session(self.页面)
                会话.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 相机["sx"] - 20, "y": 相机["sy"], "id": 1}, {"x": 相机["sx"] + 20, "y": 相机["sy"], "id": 2}]})
                会话.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 相机["sx"] - 35, "y": 相机["sy"], "id": 1}, {"x": 相机["sx"] + 35, "y": 相机["sy"], "id": 2}]})
                会话.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
                self.页面.wait_for_timeout(500)
                assert self._读取相机()["zoom"] > 相机["zoom"], (相机, self._读取相机(), 触点元素)
            if arg_减少动态:
                self.页面.wait_for_timeout(500)
                绘制前 = self.页面.evaluate("window.__metrics.draws")
                self.页面.wait_for_timeout(300)
                assert self.页面.evaluate("window.__metrics.draws") == 绘制前
            self.页面.screenshot(path=str(self.输出目录 / f"{arg_关卡标识}-{arg_手机}-final.png"))
            self.结果.append({"map": arg_关卡标识, "phoneViewport": arg_手机, "reducedMotion": arg_减少动态, "rotationZoomStable": True, "contextTile": 1, "labelsUpright": True, "edgeMenu": True})
            print(f"[完成] {arg_关卡标识} 手机视口={arg_手机} 减少动态={arg_减少动态}", flush=True)
        finally:
            上下文.close()
        assert not self.页面错误, self.页面错误

    def api_验证屋顶(self) -> None:
        原始存档 = fixture("const {levelConfig}=await import('./.test-dist/core/level-data.js');game=act(createGame(17,{...cfg,...levelConfig('classic-24'),players:cfg.players}),'start_game');game={...game,tiles:game.tiles.map(t=>t.id===1?{...t,ownerId:'p1',level:2}:t)};")
        self.关卡 = next(关卡 for 关卡 in self.关卡目录 if 关卡["map"]["id"] == "classic-24")
        上下文 = self.浏览器.new_context(viewport={"width": 1440, "height": 900})
        self.页面 = 上下文.new_page()
        try:
            load_fixture(self.页面, self.网址, 原始存档, "屋顶归属压力夹具")
            设置地图视角(self.页面, 'follow')
            self.页面.wait_for_timeout(800)
            相机 = self._读取相机()
            地块 = self.关卡["world"]["tiles"][1]
            横差, 纵差 = 地块["lotX"] - 相机["x"], 地块["lotZ"] - 相机["z"]
            横坐标 = 相机["sx"] + (横差 * math.cos(相机["yaw"]) - 纵差 * math.sin(相机["yaw"])) * 相机["zoom"]
            纵坐标 = 相机["sy"] + (横差 * math.sin(相机["yaw"]) + 纵差 * math.cos(相机["yaw"])) * math.sin(相机["elevation"]) * 相机["zoom"] + (.3 - 1.58) * math.cos(相机["elevation"]) * 相机["zoom"]
            self.页面.mouse.click(横坐标, 纵坐标, button="right")
            self.页面.get_by_role("menu").wait_for()
            assert self.页面.locator(".map-context-summary strong").inner_text().startswith("2 ·")
            assert "2 级" in self.页面.locator(".map-context-summary").inner_text()
            self.页面.screenshot(path=str(self.输出目录 / "built-roof-menu.png"))
            self.页面.keyboard.press("Escape")
            长按显示详情(self.页面, 横坐标, 纵坐标)
            assert self.页面.get_by_role("tooltip").locator("strong").inner_text().startswith("2 ·")
            松开详情(self.页面)
            self.结果.append({"holdRoof": True, "builtRoofTile": 1, "level": 2, "correctContext": True})
            print("[完成] 已建房屋屋顶右键识别所属地产", flush=True)
        finally:
            上下文.close()


# ◍ 运行
if __name__ == "__main__":
    输出目录 = Path("artifacts/map-camera-ux")
    输出目录.mkdir(parents=True, exist_ok=True)
    服务器 = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    线程 = Thread(target=服务器.serve_forever, daemon=True)
    线程.start()
    try:
        with sync_playwright() as 驱动:
            浏览器 = 驱动.chromium.launch(channel="chrome", headless=True)
            try:
                验收 = 地图交互验收_类(浏览器, f"http://127.0.0.1:{服务器.server_port}/ReactMono/", 输出目录)
                for 关卡标识, 手机, 减少动态 in [("classic-24", False, False), ("ridges-360", False, True), ("classic-24", True, False), ("ridges-360", True, True)]:
                    验收.api_验证(关卡标识, 手机, 减少动态)
                验收.api_验证屋顶()
                (输出目录 / "acceptance.json").write_text(json.dumps({"results": 验收.结果, "errors": 验收.页面错误}, ensure_ascii=False, indent=2))
            finally:
                浏览器.close()
    finally:
        服务器.shutdown()
        服务器.server_close()
        线程.join()

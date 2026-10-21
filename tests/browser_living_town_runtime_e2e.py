"""真实小镇反复遮挡/旋转/缩放后的资源回收检查。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json

from playwright.sync_api import Page, sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import load_fixture


# ◕ 功能
class 街区资源验收_类:
    """同一真实Canvas内反复创建和移除建筑淡出批次。

    更新日志：
    2026.10.21：增加同一局面跨视角淡出与恢复的资源稳定检查。
    """

    def _旋转(self, arg_页面: Page) -> None:
        宽 = arg_页面.viewport_size['width']
        横 = 宽 * 0.48
        arg_页面.mouse.move(横, 430)
        arg_页面.mouse.down(button='middle')
        arg_页面.mouse.move(横 + min(180, 宽 * 0.45), 450, steps=12)
        arg_页面.mouse.up(button='middle')
        arg_页面.wait_for_timeout(650)

    def api_执行(self) -> None:
        输出 = Path('artifacts/living-town')
        输出.mkdir(parents=True, exist_ok=True)
        样本 = Path('docs/living-town/evidence/town-state.json').read_bytes()
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        错误 = []
        结果 = []
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 手机 in [False, True]:
                    上下文 = 浏览器.new_context(viewport={'width': 390 if 手机 else 1440, 'height': 844 if 手机 else 900})
                    页面 = 上下文.new_page()
                    页面.on('pageerror', lambda arg_错误: 错误.append(str(arg_错误)))
                    页面.on('console', lambda arg_消息: 错误.append(arg_消息.text) if arg_消息.type == 'error' else None)
                    load_fixture(页面, 地址, 样本, '生活街区资源复验')
                    采样 = []
                    遮挡集合 = set()
                    for 次数 in range(6):
                        页面.get_by_role('button', name='查看全图', exact=True).click()
                        页面.wait_for_timeout(650)
                        self._旋转(页面)
                        遮挡集合.add(页面.locator('.canvas-shell').get_attribute('data-cutaway-buildings'))
                        print(f'[信息] 旋转后：phone={手机} yaw={页面.locator(".canvas-shell").get_attribute("data-camera-yaw")} cutaway={页面.locator(".canvas-shell").get_attribute("data-cutaway-buildings")}', flush=True)
                        页面.get_by_role('button', name='视角回正', exact=True).click()
                        页面.get_by_role('button', name='定位当前玩家', exact=True).click()
                        页面.wait_for_timeout(1100)
                        壳 = 页面.locator('.canvas-shell')
                        遮挡集合.add(壳.get_attribute('data-cutaway-buildings'))
                        采样.append(json.loads(壳.get_attribute('data-render-stats')))
                        print(f'[信息] 街区资源：phone={手机} cycle={次数} stats={采样[-1]}', flush=True)
                    assert len(遮挡集合) > 1, 遮挡集合
                    assert 采样[-1]['textures'] == 采样[0]['textures'], 采样
                    assert 采样[-1]['geometries'] <= 采样[0]['geometries'] + 2, 采样
                    assert all(s['pixelRatio'] > 0 and s['calls'] > 0 for s in 采样), 采样
                    页面.screenshot(path=str(输出 / f'cycles-{"phone" if 手机 else "desktop"}.png'))
                    结果.append({'phone': 手机, 'samples': 采样, 'cutawaySets': sorted(遮挡集合)})
                    上下文.close()
                浏览器.close()
            assert not 错误, 错误
            (输出 / 'runtime.json').write_text(json.dumps({'results': 结果, 'errors': 错误, 'physicalPhones': 0}, ensure_ascii=False, indent=2))
            print('[完成] 同一Canvas双视口各六轮导航和遮挡切换资源稳定。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    街区资源验收_类().api_执行()

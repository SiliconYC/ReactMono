"""生活街区：新局与固定已建局的真实双视口画面。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import os

from playwright.sync_api import Page, sync_playwright
import browser_live_e2e
from browser_live_e2e import Handler
from browser_main_game_acceptance import fixture, load_fixture


# ◕ 功能
class 生活街区验收_类:
    """使用正式存档和公开镜头控件留存视觉证据。

    更新日志：
    2026.10.21：增加新局、中央街区、已建状态和旋转的双视口对照。
    """

    def _等待镜头(self, arg_页面: Page) -> None:
        arg_页面.wait_for_function("""() => {
          const e=document.querySelector('.canvas-shell'),p=JSON.parse(e.dataset.cameraProjection);
          p.insets=e.dataset.cameraInsets;
          const old=window.__livingProjection;window.__livingProjection=p;
          const same=old&&old.insets===p.insets&&['zoom','x','z','yaw','elevation'].every(k=>Math.abs(old[k]-p[k])<1e-7);
          window.__livingStable=same?(window.__livingStable??0)+1:0;
          return window.__livingStable>=3;
        }""")
        arg_页面.wait_for_timeout(300)

    def api_执行(self) -> None:
        阶段 = os.environ.get('LIVING_PHASE', 'after')
        输出 = Path(os.environ.get('LIVING_EVIDENCE_DIR', 'docs/living-town/evidence'))
        输出.mkdir(parents=True, exist_ok=True)
        if 'LIVING_BASELINE_ROOT' in os.environ:
            browser_live_e2e.ROOT = Path(os.environ['LIVING_BASELINE_ROOT'])
        新局路径 = 输出 / 'fresh-state.json'
        if not 新局路径.exists():
            新局路径.write_bytes(fixture("""
            cfg.players=[0,1,2,3].map(i=>({id:'p'+(i+1),name:['珊瑚','晴蓝','薄荷','金橘'][i],kind:'human'}));
            game=act(createGame(17,cfg),'start_game');
            """))
        样本 = {'fresh': 新局路径.read_bytes(), 'built': (输出 / 'town-state.json').read_bytes()}
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        记录 = []
        错误 = []
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 手机 in [False, True]:
                    视口 = {'width': 390 if 手机 else 1440, 'height': 844 if 手机 else 900}
                    上下文 = 浏览器.new_context(viewport=视口, device_scale_factor=1, reduced_motion='reduce')
                    页面 = 上下文.new_page()
                    页面.on('pageerror', lambda arg_错误: 错误.append(str(arg_错误)))
                    for 名称, 存档 in 样本.items():
                        load_fixture(页面, 地址, 存档, '生活街区' + 名称)
                        页面.get_by_role('button', name='查看全图', exact=True).click()
                        for 模式 in ['overview', 'district']:
                            if 模式 == 'district':
                                for _ in range(4 if 手机 else 2):
                                    页面.get_by_role('button', name='放大地图', exact=True).click()
                            self._等待镜头(页面)
                            相机 = 页面.locator('.canvas-shell').evaluate('(e)=>({...e.dataset})')
                            if 阶段 == 'after':
                                基线 = json.loads((输出 / 'living-before.json').read_text())
                                旧 = next(r for r in 基线['results'] if r['phone'] == 手机 and r['state'] == 名称 and r['mode'] == 模式)['camera']
                                for 键 in ['cameraMode', 'cameraInsets', 'cameraCenter', 'cameraYaw', 'cameraElevation', 'cameraZoom']:
                                    assert 相机[键] == 旧[键], (名称, 手机, 模式, 键)
                            页面.screenshot(path=str(输出 / f'{阶段}-{名称}-{"phone" if 手机 else "desktop"}-{模式}.png'))
                            记录.append({'phone': 手机, 'state': 名称, 'mode': 模式, 'camera': 相机})
                        if not 手机:
                            页面.mouse.move(800, 430)
                            页面.mouse.down(button='middle')
                            页面.mouse.move(1000, 460, steps=12)
                            页面.mouse.up(button='middle')
                            self._等待镜头(页面)
                            页面.screenshot(path=str(输出 / f'{阶段}-{名称}-desktop-district-rotated.png'))
                    上下文.close()
                浏览器.close()
            assert not 错误, 错误
            (输出 / f'living-{阶段}.json').write_text(json.dumps({
                'results': 记录,
                'fixtureSha256': {k: hashlib.sha256(v).hexdigest() for k, v in 样本.items()},
                'errors': 错误,
                'physicalPhones': 0,
            }, ensure_ascii=False, indent=2))
            print(f'[完成] 生活街区 {阶段}：{len(记录)} 组真实主程序画面，页面错误为空。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    生活街区验收_类().api_执行()

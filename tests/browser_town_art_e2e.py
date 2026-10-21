"""晴湾花园同局面真实主程序画面与镜头证据。"""

# ◑ 导入
from pathlib import Path
from http.server import ThreadingHTTPServer
from threading import Thread
import hashlib
import json
import os
import math
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import fixture, load_fixture

# ◕ 功能
class 小镇验收_类:
    """通过正式存档入口捕获固定局面，不接触 React 内部状态。

    更新日志：
    2026.10.21：增加四业主、分级住宅、抵押与双视口固定镜头对比。
    """

    def api_执行(self) -> None:
        阶段 = os.environ.get('TOWN_PHASE', 'after')
        输出 = Path('docs/town-art/evidence')
        输出.mkdir(parents=True, exist_ok=True)
        样本路径 = 输出 / 'town-state.json'
        if 阶段 == 'before':
            样本 = fixture("""
            cfg.players=[0,1,2,3].map((i)=>({id:'p'+(i+1),name:['珊瑚','晴蓝','薄荷','金橘'][i],kind:'human'}));
            game=act(createGame(17,cfg),'start_game');
            const plots={1:['p1',1],2:['p1',2],4:['p2',2],5:['p2',2],7:['p3',0],8:['p3',1],10:['p4',2],11:['p4',1],13:['p1',0],14:['p2',1],16:['p3',2],17:['p3',2],19:['p4',1]};
            game={...game,players:game.players.map(p=>({...p,position:1})),tiles:game.tiles.map(t=>plots[t.id]?{...t,ownerId:plots[t.id][0],level:plots[t.id][1],...(t.id===11?{mortgaged:true}:{})}:t)};
            """)
            样本路径.write_bytes(样本)
        样本 = 样本路径.read_bytes()
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
                    上下文 = 浏览器.new_context(viewport={'width':390 if 手机 else 1440,'height':844 if 手机 else 900}, device_scale_factor=1, reduced_motion='reduce')
                    页面 = 上下文.new_page()
                    页面.on('pageerror', lambda arg_错误: 错误.append(str(arg_错误)))
                    load_fixture(页面, 地址, 样本, '晴湾美术固定局面')
                    for 模式, 按钮 in [('overview','查看全图'),('near','定位当前玩家')]:
                        页面.get_by_role('button', name=按钮, exact=True).click()
                        页面.wait_for_timeout(1800)
                        if 阶段 == 'after':
                            基线 = json.loads((输出 / 'before.json').read_text())
                            目标 = next(r for r in 基线['results'] if r['phone'] == 手机 and r['mode'] == 模式)['camera']
                            当前 = float(页面.locator('.canvas-shell').get_attribute('data-camera-zoom'))
                            页面.mouse.move(页面.viewport_size['width']*.55, 页面.viewport_size['height']*.45)
                            页面.mouse.wheel(0, -math.log(float(目标['cameraZoom'])/当前)/.0018)
                            页面.wait_for_timeout(1200)
                            for 键 in ['cameraYaw','cameraElevation','cameraCenter']:
                                assert 页面.locator('.canvas-shell').evaluate('(e,k)=>e.dataset[k]', 键) == 目标[键]
                            assert abs(float(页面.locator('.canvas-shell').get_attribute('data-camera-zoom'))-float(目标['cameraZoom'])) < .025
                        页面.screenshot(path=str(输出 / f'{阶段}-{"phone" if 手机 else "desktop"}-{模式}.png'))
                        记录.append({'phone':手机,'mode':模式,'camera':页面.locator('.canvas-shell').evaluate('(e)=>({...e.dataset})')})
                    if not 手机:
                        画布 = 页面.locator('canvas').bounding_box()
                        页面.mouse.move(画布['width']*.52, 画布['height']*.45)
                        页面.mouse.down(button='middle')
                        页面.mouse.move(画布['width']*.52+200, 画布['height']*.45+30, steps=12)
                        页面.mouse.up(button='middle')
                        页面.wait_for_timeout(1800)
                        页面.screenshot(path=str(输出 / f'{阶段}-desktop-rotated.png'))
                    上下文.close()
                浏览器.close()
            assert not 错误, 错误
            (输出 / f'{阶段}.json').write_text(json.dumps({'fixtureSha256':hashlib.sha256(样本).hexdigest(),'results':记录,'errors':错误,'physicalPhones':0,'fixtureNote':'正式序列化并导入的受控视觉样本，非自然养成对局'},ensure_ascii=False,indent=2))
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()

# ◍ 运行
if __name__ == '__main__':
    小镇验收_类().api_执行()

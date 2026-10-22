"""青柠游园住宅分级、真实建设动画与减少动态验收。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import re
import subprocess

from playwright.sync_api import Page, sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import load_fixture, export_current


# ◕ 功能
class 游园建设验收_类:
    """通过真实建设操作观察动画，并用公开存档验证实际等级。

    更新日志：
    2026.10.22 - 覆盖一级新建、二级升级、减少动态和满建样本。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/garden-depth')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.结果: list[dict] = []

    def _样本(self, arg_等级: int) -> bytes:
        代码 = """
import {createGame,applyAction} from './.test-dist/core/game.js';
import {levelConfig} from './.test-dist/core/level-data.js';
import {serializeGame} from './.test-dist/core/save.js';
const cfg={...levelConfig('lime-garden-30'),players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}],propertyVisitOnly:true,strategyEnabled:true,specialEnabled:true};
let game=applyAction(createGame(2,cfg),{type:'start_game',actorId:'p1'}).state;
game.tiles[1].ownerId='p1';game.tiles[1].level=LEVEL;
game=applyAction(game,{type:'roll',actorId:'p1'}).state;
console.log(serializeGame(game));
""".replace('LEVEL', str(arg_等级))
        return subprocess.check_output(['node', '--input-type=module', '-e', 代码], text=True).strip().encode()

    def _建设(
        self,
        arg_页面: Page,
        arg_地址: str,
        arg_等级: int,
        arg_减少动态: bool,
        arg_后缀: str,
    ) -> None:
        load_fixture(arg_页面, arg_地址, self._样本(arg_等级), f'建设{arg_等级}-{arg_后缀}')
        壳 = arg_页面.locator('.canvas-shell')
        assert 壳.get_attribute('data-construction-tiles') == ''
        arg_页面.get_by_role('button', name='定位当前玩家', exact=True).click()
        arg_页面.wait_for_timeout(800)
        arg_页面.screenshot(path=str(self.输出 / f'before-level{arg_等级 + 1}-{arg_后缀}.png'))
        arg_页面.get_by_role('button', name=re.compile('^建造住宅' if arg_等级 == 0 else '^升级房屋')).click()
        if arg_减少动态:
            arg_页面.wait_for_timeout(120)
            assert 壳.get_attribute('data-construction-tiles') == ''
        else:
            arg_页面.wait_for_function("document.querySelector('.canvas-shell')?.dataset.constructionTiles === '1'", timeout=5000, polling=10)
            arg_页面.screenshot(path=str(self.输出 / f'animating-level{arg_等级 + 1}-{arg_后缀}.png'))
            arg_页面.wait_for_function("document.querySelector('.canvas-shell')?.dataset.constructionTiles === ''", timeout=5000)
        arg_页面.screenshot(path=str(self.输出 / f'completed-level{arg_等级 + 1}-{arg_后缀}.png'))
        对局, _ = export_current(arg_页面)
        assert 对局['tiles'][1]['level'] == arg_等级 + 1
        assert 对局['tiles'][1]['ownerId'] == 'p1'
        self.结果.append({'viewport': arg_后缀, 'level': arg_等级 + 1, 'reducedMotion': arg_减少动态, 'settled': True})

    def api_执行(self) -> None:
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 手机, 减少 in [(False, False), (True, False), (False, True)]:
                    上下文 = 浏览器.new_context(viewport={'width': 390 if 手机 else 1440, 'height': 844 if 手机 else 900}, reduced_motion='reduce' if 减少 else 'no-preference', accept_downloads=True)
                    页面 = 上下文.new_page()
                    页面.on('dialog', lambda arg_对话: arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None))
                    页面.on('pageerror', lambda arg_错: self.错误.append(str(arg_错)))
                    页面.on('console', lambda arg_消息: self.错误.append(arg_消息.text) if arg_消息.type == 'error' else None)
                    后缀 = 'reduced' if 减少 else 'phone' if 手机 else 'desktop'
                    for 等级 in [0, 1]:
                        self._建设(页面, 地址, 等级, 减少, 后缀)
                    上下文.close()
                浏览器.close()
            assert not self.错误, self.错误
            (self.输出 / 'construction-report.json').write_text(json.dumps({'results': self.结果, 'errors': self.错误, 'physicalPhone': False}, ensure_ascii=False, indent=2))
            print('[完成] 一级新建、二级升级在双视口有真实动画，减少动态直接落定，存档等级正确。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    游园建设验收_类().api_执行()

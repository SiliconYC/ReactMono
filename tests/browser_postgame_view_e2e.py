"""终局默认不遮挡棋盘，允许浏览并主动查看结算。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import os
import subprocess

from playwright.sync_api import Page, sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import export_current, load_fixture, open_panel


# ◕ 功能
class 终局观赏验收_类:
    """从公开存档和真实结束回合入口验证终局交互。

    更新日志：
    2026.10.22 - 覆盖轮数获胜、破产、平局及终局地图和资产浏览。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/postgame-view')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.结果: list[dict] = []

    def _样本(self, arg_模式: str) -> bytes:
        代码 = """
import {createGame,applyAction} from './.test-dist/core/game.js';
import {levelConfig} from './.test-dist/core/level-data.js';
import {serializeGame} from './.test-dist/core/save.js';
const cfg={...levelConfig('lime-garden-30'),maxRounds:1,initialCash:3000,players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}],propertyVisitOnly:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,stockAccount:'bank',strategyEnabled:true,specialEnabled:true};
let game=applyAction(createGame(17,cfg),{type:'start_game',actorId:'p1'}).state;
const mode=MODE;
if(mode==='bankruptcy'){
 game={...game,pendingDie:1,players:game.players.map((p,i)=>i===0?{...p,cash:1}:p),tiles:game.tiles.map(t=>t.kind==='property'?{...t,ownerId:'p2',level:2}:t)};
 game=applyAction(game,{type:'roll',actorId:'p1'}).state;
}else if(mode!=='worker'){
 game={...game,phase:'await_end_turn',currentPlayerIndex:1,tiles:game.tiles.map(t=>mode==='draw'||t.kind!=='property'?t:{...t,ownerId:t.id%2?'p1':'p2',level:t.id%3})};
 if(mode!=='live')game=applyAction(game,{type:'end_turn',actorId:'p2'}).state;
}
console.log(serializeGame(game));
""".replace('MODE', json.dumps(arg_模式))
        return subprocess.check_output(['node', '--input-type=module', '-e', 代码], text=True).strip().encode()

    def _检查终局(self, arg_页面: Page) -> None:
        assert arg_页面.locator('main').get_attribute('data-game-status') == 'finished'
        assert arg_页面.locator('.result-layer').count() == 0, '终局仍存在覆盖全屏的结算层'
        assert arg_页面.locator('dialog[open]').count() == 0, '终局不应主动打开模态结算'
        assert arg_页面.locator('.result-box').count() == 1
        assert arg_页面.get_by_role('button', name='掷骰前进', exact=False).count() == 0
        assert arg_页面.locator('.action-buttons .primary-btn').count() == 0
        assert arg_页面.locator('.player-roster').get_by_text('行动中', exact=True).count() == 0
        assert arg_页面.evaluate("document.elementFromPoint(innerWidth*.5,innerHeight*.45)?.tagName === 'CANVAS'")

    def _浏览(self, arg_页面: Page) -> None:
        壳 = arg_页面.locator('.canvas-shell')
        arg_页面.get_by_role('button', name='查看全图', exact=True).click()
        arg_页面.wait_for_timeout(700)
        旋角 = float(壳.get_attribute('data-camera-yaw'))
        横 = arg_页面.viewport_size['width'] * .5
        纵 = arg_页面.viewport_size['height'] * .45
        arg_页面.mouse.move(横, 纵)
        arg_页面.mouse.down(button='middle')
        arg_页面.mouse.move(横 + 60, 纵 - 30, steps=12)
        arg_页面.mouse.up(button='middle')
        arg_页面.wait_for_timeout(700)
        assert abs(float(壳.get_attribute('data-camera-yaw')) - 旋角) > .05
        缩放 = float(壳.get_attribute('data-camera-zoom'))
        arg_页面.get_by_role('button', name='放大地图', exact=True).click()
        arg_页面.wait_for_timeout(700)
        assert float(壳.get_attribute('data-camera-zoom')) > 缩放 * 1.15
        arg_页面.get_by_role('button', name='查看结算', exact=True).click()
        arg_页面.get_by_role('dialog', name='对局结算', exact=True).wait_for()
        assert arg_页面.locator('.postgame-ranking li').count() == 2
        arg_页面.keyboard.press('Escape')
        assert arg_页面.locator('dialog[open]').count() == 0
        arg_页面.locator('.player-roster button').first.click()
        arg_页面.get_by_role('dialog', name='玩家资产', exact=True).wait_for()
        assert arg_页面.locator('.asset-player').count() == 2
        arg_页面.keyboard.press('Escape')

    def api_执行(self) -> None:
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 手机 in [False, True]:
                    上下文 = 浏览器.new_context(viewport={'width': 390 if 手机 else 1440, 'height': 844 if 手机 else 900}, reduced_motion='reduce', accept_downloads=True)
                    页面 = 上下文.new_page()
                    页面.on('pageerror', lambda arg_错: self.错误.append(str(arg_错)))
                    页面.on('console', lambda arg_消息: self.错误.append(arg_消息.text) if arg_消息.type == 'error' else None)
                    页面.on('dialog', lambda arg_对话: arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None))
                    for 模式 in (['worker'] if os.environ.get('POSTGAME_ONLY_WORKER') == '1' else ['rounds', 'bankruptcy', 'draw', 'live', 'worker']):
                        原文 = self._样本(模式)
                        load_fixture(页面, 地址, 原文, f'观赏-{模式}')
                        if 模式 == 'live':
                            页面.get_by_role('button', name='结束当前回合', exact=False).click()
                            页面.locator('.result-box').wait_for(timeout=10000)
                        if 模式 == 'worker':
                            open_panel(页面, '调试工具')
                            页面.get_by_label('推进轮数', exact=True).fill('40')
                            页面.get_by_role('button', name='一键模拟', exact=True).click()
                            页面.locator('main[data-game-status="finished"]').wait_for()
                            页面.locator('.result-box').wait_for(timeout=10000)
                        self._检查终局(页面)
                        保存前, _ = export_current(页面)
                        if 模式 not in ['live', 'worker']:
                            assert 保存前 == json.loads(原文)['game']
                        self._浏览(页面)
                        保存后, _ = export_current(页面)
                        assert 保存后 == 保存前
                        页面.screenshot(path=str(self.输出 / f'{模式}-{"phone" if 手机 else "desktop"}.png'))
                        self.结果.append({'mode': 模式, 'phone': 手机, 'unobstructed': True, 'navigation': True, 'readOnly': True, 'saveUnchanged': True})
                    上下文.close()
                浏览器.close()
            assert not self.错误, self.错误
            (self.输出 / 'report.json').write_text(json.dumps({'results': self.结果, 'errors': self.错误, 'physicalPhone': False}, ensure_ascii=False, indent=2))
            print('[完成] 双视口五类终局默认无模态遮挡，可浏览/主动查看排名和资产，存档局面不变。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    终局观赏验收_类().api_执行()

"""青柠游园：真实生产页面的独立关卡、对局和双视口验收。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import math
import re
import subprocess

from playwright.sync_api import Page, sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, open_saved_games, select_map
from browser_main_game_acceptance import load_fixture, open_panel, export_current


# ◕ 功能
class 青柠游园验收_类:
    """使用公开存档入口和真实鼠标验证新关卡。

    更新日志：
    2026.10.22 - 增加新局购地、建设、存读档、双视口导航及满建画面验收。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/lime-garden')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.结果: list[dict] = []

    def _样本(self, arg_内容: str) -> bytes:
        代码 = """
import {createGame,applyAction} from './.test-dist/core/game.js';
import {levelConfig} from './.test-dist/core/level-data.js';
import {serializeGame} from './.test-dist/core/save.js';
const config={...levelConfig('lime-garden-30'),players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}],propertyVisitOnly:true,strategyEnabled:true,specialEnabled:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,maxRounds:2};
let game=applyAction(createGame(2,config),{type:'start_game',actorId:'p1'}).state;
""" + arg_内容 + "\nconsole.log(serializeGame(game));"
        return subprocess.check_output(['node', '--input-type=module', '-e', 代码], text=True).strip().encode()

    def _截图(self, arg_页面: Page, arg_名称: str) -> None:
        arg_页面.wait_for_timeout(850)
        arg_页面.screenshot(path=str(self.输出 / (arg_名称 + '.png')))

    def _导航(self, arg_页面: Page) -> None:
        壳 = arg_页面.locator('.canvas-shell')
        原值 = float(壳.get_attribute('data-camera-yaw'))
        横 = arg_页面.viewport_size['width'] * .5
        arg_页面.mouse.move(横, 340)
        arg_页面.mouse.down(button='middle')
        arg_页面.mouse.move(横 + 75, 300, steps=12)
        arg_页面.mouse.up(button='middle')
        arg_页面.wait_for_timeout(700)
        assert abs(float(壳.get_attribute('data-camera-yaw')) - 原值) > .05
        arg_页面.get_by_role('button', name='视角回正', exact=True).click()
        arg_页面.get_by_role('button', name='查看全图', exact=True).click()
        arg_页面.wait_for_timeout(700)
        缩放 = float(壳.get_attribute('data-camera-zoom'))
        arg_页面.get_by_role('button', name='放大地图', exact=True).click()
        arg_页面.wait_for_timeout(700)
        assert float(壳.get_attribute('data-camera-zoom')) > 缩放 * 1.15

    def _选格(self, arg_页面: Page) -> None:
        壳 = arg_页面.locator('.canvas-shell')
        投影 = json.loads(壳.get_attribute('data-camera-projection'))
        边距 = json.loads(壳.get_attribute('data-camera-insets'))
        宽 = arg_页面.viewport_size['width']
        高 = arg_页面.viewport_size['height']
        横 = 1 - 投影['x']
        纵 = -7 - 投影['z']
        角 = 投影['yaw']
        俯角 = 投影['elevation']
        屏横 = 宽 / 2 + (边距['left'] - 边距['right']) / 2 + (横 * math.cos(角) - 纵 * math.sin(角)) * 投影['zoom']
        屏纵 = 高 / 2 - (边距['bottom'] - 边距['top']) / 2 + ((横 * math.sin(角) + 纵 * math.cos(角)) * math.sin(俯角) + .53 * math.cos(俯角)) * 投影['zoom']
        arg_页面.mouse.click(屏横, 屏纵)
        arg_页面.get_by_role('button', name='关闭地块详情', exact=True).wait_for()
        assert '蜜桃庭院' in arg_页面.locator('.board-inspector').inner_text()
        arg_页面.get_by_role('button', name='关闭地块详情', exact=True).click()

    def _购地(self, arg_页面: Page) -> None:
        arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
        购买 = arg_页面.get_by_role('button', name=re.compile('^购买地产'))
        购买.wait_for(timeout=20000)
        购买.click()
        arg_页面.get_by_role('button', name=re.compile('^结束当前回合')).wait_for()
        arg_页面.on('dialog', lambda arg_对话: arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None))
        对局, 原文 = export_current(arg_页面)
        assert 对局['map']['id'] == 'lime-garden-30'
        assert len(对局['tiles']) == 30
        assert 对局['tiles'][1]['ownerId'] == 'p1'
        (self.输出 / 'purchased-state.json').write_bytes(原文)

    def _终局(self, arg_页面: Page) -> None:
        for _ in range(120):
            if arg_页面.locator('main[data-game-status="finished"]').count():
                return
            for 名称 in ['掷骰前进', '购买地产', '暂不购买', '暂不建设', '结束当前回合', '离开商店', '跳过当前停留回合', '我已就位，开始操作', '开始回合', '确认操作']:
                按钮 = arg_页面.get_by_role('button', name=re.compile('^' + 名称))
                if 按钮.count() and 按钮.first.is_enabled():
                    按钮.first.click()
                    break
            arg_页面.wait_for_timeout(150)
        self._截图(arg_页面, 'failed-match')
        raise AssertionError(arg_页面.locator('button:visible').all_text_contents())

    def api_执行(self) -> None:
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 手机 in [False, True]:
                    上下文 = 浏览器.new_context(viewport={'width': 390 if 手机 else 1440, 'height': 844 if 手机 else 900}, accept_downloads=True)
                    页面 = 上下文.new_page()
                    页面.on('pageerror', lambda arg_错: self.错误.append(str(arg_错)))
                    页面.on('console', lambda arg_消息: self.错误.append(arg_消息.text) if arg_消息.type == 'error' else None)
                    页面.goto(地址)
                    open_new_game_setup(页面)
                    assert 页面.locator('.setup-map-choice button').count() == 6
                    select_map(页面, 'lime-garden-30')
                    页面.get_by_label('对局种子').fill('2')
                    页面.get_by_label('最多轮数').fill('2')
                    页面.get_by_label('快速模式').check()
                    页面.get_by_label('第 2 位玩家类型').select_option('human')
                    页面.get_by_role('button', name='开始游戏', exact=True).click()
                    页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
                    assert 页面.locator('main').get_attribute('data-map-id') == 'lime-garden-30'
                    页面.get_by_role('button', name='查看全图', exact=True).click()
                    后缀 = 'phone' if 手机 else 'desktop'
                    self._截图(页面, 'overview-' + 后缀)
                    self._选格(页面)
                    self._导航(页面)
                    self._截图(页面, 'detail-' + 后缀)
                    self._购地(页面)
                    self._终局(页面)
                    self._截图(页面, 'finished-' + 后缀)
                    建设 = self._样本("""
game.tiles[1].ownerId='p1';
game=applyAction(game,{type:'roll',actorId:'p1'}).state;
""")
                    load_fixture(页面, 地址, 建设, '游园建设-' + 后缀)
                    页面.get_by_role('button', name=re.compile('^建造住宅')).click()
                    if 页面.get_by_role('heading', name='确认操作', exact=True).count():
                        页面.get_by_role('button', name='确认操作', exact=True).click()
                    对局, _ = export_current(页面)
                    assert 对局['tiles'][1]['level'] == 1
                    满建 = self._样本("""
game.tiles=game.tiles.map(t=>t.kind==='property'?{...t,ownerId:t.id%2?'p1':'p2',level:t.id%3}:t);
""")
                    load_fixture(页面, 地址, 满建, '游园满建-' + 后缀)
                    页面.get_by_role('button', name='查看全图', exact=True).click()
                    self._截图(页面, 'populated-' + 后缀)
                    self._导航(页面)
                    self._截图(页面, 'populated-detail-' + 后缀)
                    保存前, _ = export_current(页面)
                    assert 保存前 == json.loads(满建)['game']
                    页面.reload()
                    open_saved_games(页面)
                    页面.locator('.save-list li, .title-save-list li').filter(has=页面.get_by_text('当前验收', exact=True)).first.get_by_role('button', name='读取', exact=True).click()
                    页面.locator('main[data-map-id="lime-garden-30"]').wait_for()
                    页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
                    保存后, _ = export_current(页面)
                    assert 保存后 == 保存前
                    self.结果.append({'viewport': 后缀, 'newGame': True, 'purchase': True, 'construction': True, 'completedMatch': True, 'saveRoundTrip': True, 'navigation': True})
                    上下文.close()
                浏览器.close()
            assert not self.错误, self.错误
            (self.输出 / 'browser-report.json').write_text(json.dumps({'results': self.结果, 'errors': self.错误, 'physicalPhone': False}, ensure_ascii=False, indent=2))
            print('[完成] 青柠游园桌面与手机视口：新局、购地、建设、完整结算、存读档与导航通过。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    青柠游园验收_类().api_执行()

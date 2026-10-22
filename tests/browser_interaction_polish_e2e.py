"""系统显示与交互修整的真实生产浏览器验收。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import math
import re
import subprocess

from playwright.sync_api import Page, sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import load_fixture, open_panel


# ◕ 功能
class 交互修整验收_类:
    """真实输入检查相机连续性、长按查看、自动衔接和命名。

    更新日志：
    2026.10.22 - 新增十二项反馈对应的桌面/手机验收。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/interaction-polish')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.结果: list[dict] = []
        self.关卡 = next(关卡 for 关卡 in json.loads(Path('src/data/levels.json').read_text())['levels'] if 关卡['map']['id'] == 'lime-garden-30')

    def _样本(self, arg_场景: str) -> bytes:
        代码 = """
import {createGame,applyAction} from './.test-dist/core/game.js';
import {levelConfig} from './.test-dist/core/level-data.js';
import {serializeGame} from './.test-dist/core/save.js';
import {simulateDebugRounds} from './.test-dist/core/debug-tools.js';
const mode=MODE;
const cfg={...levelConfig('lime-garden-30'),initialCash:3000,players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}],propertyVisitOnly:true,strategyEnabled:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,stockAccount:'bank'};
let game=applyAction(createGame(2,cfg),{type:'start_game',actorId:'p1'}).state;
if(mode==='build')for(const id of [1,2,3]){game.tiles[id].ownerId='p1';game.tiles[id].level=0;}
if(mode==='populated')for(const t of game.tiles)if(t.kind==='property'){t.ownerId=[1,2,3,9,10,11,17,18,19].includes(t.id)?'p1':'p2';t.level=t.id%2+1;}
if(mode==='pose'){game.players=game.players.map(p=>({...p,cash:1000000}));game=simulateDebugRounds(game,30).state;}
console.log(serializeGame(game));
""".replace('MODE', json.dumps(arg_场景))
        return subprocess.check_output(['node', '--input-type=module', '-e', 代码], text=True).strip().encode()

    def _相机(self, arg_页面: Page) -> dict:
        return arg_页面.locator('.canvas-shell').evaluate('e=>({p:JSON.parse(e.dataset.cameraProjection),i:JSON.parse(e.dataset.cameraInsets),mode:e.dataset.cameraMode})')

    def _投影(
        self,
        arg_页面: Page,
        arg_横: float,
        arg_纵: float,
        arg_高: float = -.23,
    ) -> tuple[float, float]:
        相机 = self._相机(arg_页面)
        投影, 边 = 相机['p'], 相机['i']
        横, 纵 = arg_横 - 投影['x'], arg_纵 - 投影['z']
        方位, 俯仰, 缩放 = 投影['yaw'], 投影['elevation'], 投影['zoom']
        屏横 = (边['left'] + arg_页面.viewport_size['width'] - 边['right']) / 2
        屏纵 = (边['top'] + arg_页面.viewport_size['height'] - 边['bottom']) / 2
        return (屏横 + (横 * math.cos(方位) - 纵 * math.sin(方位)) * 缩放,
                屏纵 + ((横 * math.sin(方位) + 纵 * math.cos(方位)) * math.sin(俯仰) - (arg_高 - .3) * math.cos(俯仰)) * 缩放)

    def _收集相机(self, arg_页面: Page) -> None:
        arg_页面.evaluate('''()=>{window.__相机=[];window.__采样=true;function sample(){const e=document.querySelector('.canvas-shell');if(e)window.__相机.push({p:JSON.parse(e.dataset.cameraProjection),i:JSON.parse(e.dataset.cameraInsets),mode:e.dataset.cameraMode});if(window.__采样)requestAnimationFrame(sample)}requestAnimationFrame(sample)}''')

    def _检查稳定(self, arg_页面: Page) -> None:
        样本 = arg_页面.evaluate('()=>{window.__采样=false;return window.__相机}')
        assert len(样本) > 15
        首 = 样本[0]
        for 末 in 样本:
            assert 末['mode'] == 'overview', 末
            assert abs(末['p']['zoom'] - 首['p']['zoom']) < .03, (首, 末)
            assert abs(末['p']['x'] - 首['p']['x']) < .01
            assert abs(末['p']['z'] - 首['p']['z']) < .01
            assert 末['i'] == 首['i']
        self.结果.append({'检查': '连续相机', '帧数': len(样本), '视口': arg_页面.viewport_size})

    def _回合(
        self,
        arg_页面: Page,
        arg_地址: str,
        arg_后缀: str,
    ) -> None:
        for 场景 in ['buy', 'build']:
            load_fixture(arg_页面, arg_地址, self._样本(场景), 场景 + arg_后缀)
            arg_页面.wait_for_timeout(900)
            self._收集相机(arg_页面)
            arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
            按钮 = arg_页面.get_by_role('button', name=re.compile('^购买地产' if 场景 == 'buy' else '^联排建造'))
            按钮.wait_for(timeout=15000)
            按钮.click()
            arg_页面.get_by_role('button', name='我已就位，开始操作').wait_for(timeout=15000)
            assert arg_页面.locator('main').get_attribute('data-game-phase') == 'await_roll'
            assert arg_页面.get_by_role('button', name='结束当前回合', exact=True).count() == 0
            self._检查稳定(arg_页面)
        load_fixture(arg_页面, arg_地址, self._样本('buy'), '经营暂停' + arg_后缀)
        arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
        arg_页面.get_by_role('button', name=re.compile('^购买地产')).click()
        arg_页面.get_by_role('button', name='管理资产', exact=True).click()
        arg_页面.get_by_role('dialog').wait_for()
        arg_页面.keyboard.press('Escape')
        arg_页面.wait_for_timeout(4300)
        assert arg_页面.locator('main').get_attribute('data-game-phase') == 'await_end_turn'
        arg_页面.get_by_role('button', name=re.compile('^继续下一位')).click()
        arg_页面.get_by_role('button', name='我已就位，开始操作').wait_for()

    def _菜单等待(self, arg_页面: Page, arg_地址: str) -> None:
        load_fixture(arg_页面, arg_地址, self._样本('buy'), '菜单暂停')
        arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
        arg_页面.get_by_role('button', name=re.compile('^购买地产')).click()
        arg_页面.get_by_role('button', name='管理资产', exact=True).wait_for()
        arg_页面.mouse.click(arg_页面.viewport_size['width'] * .55, arg_页面.viewport_size['height'] * .45, button='right')
        arg_页面.get_by_role('menu', name='地图快捷菜单').wait_for()
        arg_页面.wait_for_timeout(4300)
        assert arg_页面.locator('main').get_attribute('data-game-phase') == 'await_end_turn'
        assert arg_页面.get_by_role('menu', name='地图快捷菜单').is_visible()
        arg_页面.keyboard.press('Escape')
        arg_页面.get_by_role('button', name='我已就位，开始操作').wait_for(timeout=8000)
        self.结果.append({'检查': '右键菜单暂停交接且关闭后自动恢复'})

    def _查看(
        self,
        arg_页面: Page,
        arg_地址: str,
        arg_后缀: str,
    ) -> None:
        load_fixture(arg_页面, arg_地址, self._样本('populated'), '查看' + arg_后缀)
        arg_页面.wait_for_timeout(900)
        地块 = self.关卡['world']['tiles'][5]
        横, 纵 = self._投影(arg_页面, 地块['x'], 地块['z'])
        arg_页面.mouse.click(横, 纵)
        assert arg_页面.get_by_role('tooltip').count() == 0
        assert arg_页面.locator('.board-inspector').count() == 0
        arg_页面.mouse.move(横, 纵)
        arg_页面.mouse.down()
        arg_页面.get_by_role('tooltip').wait_for()
        assert '蜜桃庭院' in arg_页面.get_by_role('tooltip').inner_text()
        arg_页面.screenshot(path=str(self.输出 / ('land-tooltip-' + arg_后缀 + '.png')))
        arg_页面.mouse.up()
        arg_页面.get_by_role('tooltip').wait_for(state='hidden')
        姿态 = json.loads(arg_页面.locator('.canvas-shell').get_attribute('data-actor-0'))
        assert abs(姿态['yaw'] - math.pi / 2) < .001
        横, 纵 = self._投影(arg_页面, 姿态['x'], 姿态['z'], .61)
        arg_页面.mouse.move(横, 纵)
        arg_页面.mouse.down()
        arg_页面.get_by_role('tooltip').wait_for()
        assert '现金' in arg_页面.get_by_role('tooltip').inner_text()
        arg_页面.screenshot(path=str(self.输出 / ('actor-tooltip-' + arg_后缀 + '.png')))
        arg_页面.mouse.up()
        arg_页面.get_by_role('tooltip').wait_for(state='hidden')
        arg_页面.locator('canvas').focus()
        arg_页面.keyboard.down('i')
        arg_页面.get_by_role('tooltip').wait_for()
        assert '地产' in arg_页面.get_by_role('tooltip').inner_text()
        arg_页面.keyboard.up('i')
        arg_页面.get_by_role('tooltip').wait_for(state='hidden')
        arg_页面.get_by_role('button', name='地图工具', exact=True).click()
        assert arg_页面.get_by_role('button', name='放大地图').is_visible()
        arg_页面.get_by_role('button', name='地图工具', exact=True).click()
        assert arg_页面.get_by_role('button', name='放大地图').count() == 0
        self.结果.append({'检查': '长按地产/角色/键盘与紧凑控件', '视口': arg_后缀})

    def _触屏与重载朝向(self, arg_页面: Page, arg_地址: str) -> None:
        原始 = self._样本('pose')
        对局 = json.loads(原始)['game']
        load_fixture(arg_页面, arg_地址, 原始, '模拟30轮后朝向')
        for 座次, 玩家 in enumerate(对局['players']):
            姿态 = json.loads(arg_页面.locator('.canvas-shell').get_attribute('data-actor-' + str(座次)))
            当前 = self.关卡['world']['tiles'][玩家['position']]
            下格 = self.关卡['world']['tiles'][(玩家['position'] + 1) % 30]
            预期 = math.atan2(下格['x'] - 当前['x'], 下格['z'] - 当前['z'])
            assert abs(math.atan2(math.sin(姿态['yaw'] - 预期), math.cos(姿态['yaw'] - 预期))) < .001
        load_fixture(arg_页面, arg_地址, self._样本('populated'), '真实触屏查看')
        arg_页面.wait_for_timeout(700)
        地块 = self.关卡['world']['tiles'][5]
        横, 纵 = self._投影(arg_页面, 地块['x'], 地块['z'])
        协议 = arg_页面.context.new_cdp_session(arg_页面)
        触点 = {'x': 横, 'y': 纵, 'id': 1}
        协议.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [触点]})
        arg_页面.get_by_role('tooltip').wait_for()
        assert '蜜桃庭院' in arg_页面.get_by_role('tooltip').inner_text()
        协议.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [触点, {'x': 横 + 20, 'y': 纵 + 20, 'id': 2}]})
        arg_页面.get_by_role('tooltip').wait_for(state='hidden')
        协议.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        arg_页面.wait_for_timeout(500)
        assert arg_页面.get_by_role('tooltip').count() == 0
        协议.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [触点]})
        arg_页面.get_by_role('tooltip').wait_for()
        协议.send('Input.dispatchTouchEvent', {'type': 'touchCancel', 'touchPoints': []})
        arg_页面.get_by_role('tooltip').wait_for(state='hidden')
        协议.detach()
        self.结果.append({'检查': '30轮模拟读档朝向/原生触屏长按/多指取消/触屏取消'})

    def _视角(self, arg_页面: Page, arg_后缀: str) -> None:
        原 = self._相机(arg_页面)
        横 = arg_页面.viewport_size['width'] * .52
        纵 = arg_页面.viewport_size['height'] * .45
        arg_页面.mouse.move(横, 纵)
        arg_页面.mouse.down(button='middle')
        arg_页面.mouse.move(横 + 70, 纵 - 180, steps=15)
        arg_页面.mouse.up(button='middle')
        arg_页面.wait_for_timeout(900)
        后 = self._相机(arg_页面)
        assert abs(后['p']['yaw'] - 原['p']['yaw']) > .25
        assert abs(后['p']['zoom'] - 原['p']['zoom']) < .03
        assert 后['p']['elevation'] < .3
        arg_页面.screenshot(path=str(self.输出 / ('low-angle-' + arg_后缀 + '.png')))
        arg_页面.mouse.wheel(0, -100)
        arg_页面.wait_for_timeout(900)
        assert self._相机(arg_页面)['p']['zoom'] > 后['p']['zoom'] * 1.1
        self.结果.append({'检查': '中键仅旋转/低角度/滚轮缩放', '视口': arg_后缀, '俯仰度': 后['p']['elevation'] * 180 / math.pi})

    def api_执行(self) -> None:
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 后缀, 宽 in [('desktop', 1440), ('phone', 390)]:
                    上下文 = 浏览器.new_context(viewport={'width': 宽, 'height': 900 if 宽 == 1440 else 844}, has_touch=宽 == 390, accept_downloads=True)
                    上下文.add_init_script("localStorage.setItem('reactmono-camera-follow','0')")
                    页面 = 上下文.new_page()
                    页面.on('dialog', lambda arg_对话: arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None))
                    页面.on('pageerror', lambda arg_错误: self.错误.append(str(arg_错误)))
                    页面.on('console', lambda arg_消息: self.错误.append(arg_消息.text) if arg_消息.type == 'error' else None)
                    页面.goto(地址)
                    assert 页面.title() == '大富翁 2026'
                    标题 = 页面.get_by_role('heading', name='大富翁 2026', exact=True)
                    标题.wait_for()
                    self._回合(页面, 地址, 后缀)
                    self._菜单等待(页面, 地址)
                    self._查看(页面, 地址, 后缀)
                    if 后缀 == 'phone':
                        self._触屏与重载朝向(页面, 地址)
                    self._视角(页面, 后缀)
                    上下文.close()
                浏览器.close()
            assert not self.错误, self.错误
            (self.输出 / 'report.json').write_text(json.dumps({'results': self.结果, 'errors': self.错误, 'physicalPhone': False}, ensure_ascii=False, indent=2))
            print('[完成] 相机连续性、回合自动衔接、长按查看与低角度双视口验收通过。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    交互修整验收_类().api_执行()

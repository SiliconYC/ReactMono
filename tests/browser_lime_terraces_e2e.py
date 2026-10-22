"""青柠街区联排的真实交互、画面及存档验收。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import re
import subprocess

from playwright.sync_api import Page, sync_playwright
from browser_live_e2e import Handler
from browser_main_game_acceptance import (
    load_fixture, export_current, open_panel, 等待结算交接, 设置地图视角,
)


# ◕ 功能
class 联排验收_类:
    """通过公开导入入口和生产界面验收整排经营。

    更新日志：
    2026.10.22 - 覆盖满级落点补建、整排租金、双视口与原子建设费用。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/lime-terraces')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.报告: list[dict] = []

    def _样本(self, arg_场景: str) -> bytes:
        代码 = """
import {createGame,applyAction} from './.test-dist/core/game.js';
import {levelConfig} from './.test-dist/core/level-data.js';
import {serializeGame} from './.test-dist/core/save.js';
import {LIME_PROPERTY_BLOCKS} from './.test-dist/core/property-groups.js';
const mode=MODE;
const cfg={...levelConfig('lime-garden-30'),initialCash:3000,players:[{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'对手',kind:'human'}],propertyVisitOnly:true,strategyEnabled:true,bankEnabled:true,loanEnabled:true};
let game=applyAction(createGame(2,cfg),{type:'start_game',actorId:'p1'}).state;
for(const id of [1,2,3]){game.tiles[id].ownerId='p1';game.tiles[id].level=mode==='rent'?2:mode==='build'?0:id===1?2:0;}
if(mode==='poor')game.players[0].cash=100;
if(mode==='legacy')delete game.terraceRulesVersion;
if(mode==='populated')for(const [index,block] of LIME_PROPERTY_BLOCKS.entries())for(const id of block.tileIds){game.tiles[id].ownerId=index%2?'p2':'p1';game.tiles[id].level=index%3===0?1:2;}
if(mode!=='rent')game=applyAction(game,{type:'roll',actorId:'p1'}).state;
else game={...game,currentPlayerIndex:1};
console.log(serializeGame(game));
""".replace('MODE', json.dumps(arg_场景))
        return subprocess.check_output(['node', '--input-type=module', '-e', 代码], text=True).strip().encode()

    def _画面(self, arg_页面: Page, arg_名称: str) -> None:
        arg_页面.wait_for_timeout(900)
        arg_页面.screenshot(path=str(self.输出 / (arg_名称 + '.png')))

    def _补建(
        self,
        arg_页面: Page,
        arg_地址: str,
        arg_后缀: str,
    ) -> None:
        for 场景, 户数, 现金, 等级 in [('mixed', 2, 2880, [2, 1, 1]), ('build', 3, 2820, [1, 1, 1])]:
            load_fixture(arg_页面, arg_地址, self._样本(场景), 场景 + arg_后缀)
            行动 = arg_页面.get_by_role('region', name='当前行动')
            assert '柚香里 · 3 块联排' in 行动.inner_text()
            assert ('144' if 场景 == 'mixed' else '72') in 行动.inner_text()
            self._画面(arg_页面, 场景 + '-before-' + arg_后缀)
            arg_页面.get_by_role('button', name=re.compile('^联排建造 ' + str(户数))).click()
            if arg_后缀 != 'reduced':
                预期 = '2,3' if 场景 == 'mixed' else '1,2,3'
                arg_页面.wait_for_function('(expected)=>document.querySelector(".canvas-shell")?.dataset.constructionTiles===expected', arg=预期, timeout=5000, polling=10)
            等待结算交接(arg_页面)
            self._画面(arg_页面, 场景 + '-after-' + arg_后缀)
            对局, 存档 = export_current(arg_页面)
            assert [对局['tiles'][编号]['level'] for 编号 in [1, 2, 3]] == 等级
            assert 对局['players'][0]['cash'] == 现金
            assert 对局['terraceRulesVersion'] == 1
            assert arg_页面.get_by_role('button', name=re.compile('^联排建造')).count() == 0
            load_fixture(arg_页面, arg_地址, 存档, '往返-' + 场景 + arg_后缀)
            还原, _ = export_current(arg_页面)
            assert 还原 == 对局
            self.报告.append({'场景': 场景, '视口': arg_后缀, '现金': 现金, '等级': 等级, '存档往返': True})

    def _收租(
        self,
        arg_页面: Page,
        arg_地址: str,
        arg_后缀: str,
    ) -> None:
        load_fixture(arg_页面, arg_地址, self._样本('rent'), '整排租金-' + arg_后缀)
        arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
        等待结算交接(arg_页面)
        对局, _ = export_current(arg_页面)
        assert [玩家['cash'] for 玩家 in 对局['players']] == [3288, 2712]
        租金 = [事件 for 事件 in 对局['events'] if 事件['type'] == 'rent_paid']
        assert len(租金) == 1
        assert 租金[0]['details']['due'] == 租金[0]['details']['amount'] == 288
        self.报告.append({'场景': '整排收租', '视口': arg_后缀, '收费': 288, '笔数': 1})

    def api_执行(self) -> None:
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 后缀, 宽, 减少 in [('desktop', 1440, False), ('phone', 390, False), ('reduced', 1440, True)]:
                    上下文 = 浏览器.new_context(viewport={'width': 宽, 'height': 900 if 宽 == 1440 else 844}, reduced_motion='reduce' if 减少 else 'no-preference', accept_downloads=True)
                    页面 = 上下文.new_page()
                    页面.on('dialog', lambda arg_对话: arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None))
                    页面.on('pageerror', lambda arg_错: self.错误.append(str(arg_错)))
                    页面.on('console', lambda arg_消息: self.错误.append(arg_消息.text) if arg_消息.type == 'error' else None)
                    self._补建(页面, 地址, 后缀)
                    self._收租(页面, 地址, 后缀)
                    load_fixture(页面, 地址, self._样本('poor'), '不足整排-' + 后缀)
                    assert not 页面.get_by_role('button', name=re.compile('^联排建造 2')).is_enabled()
                    load_fixture(页面, 地址, self._样本('legacy'), '旧档-' + 后缀)
                    assert 页面.get_by_role('button', name=re.compile('^联排建造')).count() == 0
                    open_panel(页面, '玩法说明')
                    assert '旧版单地块规则' in 页面.get_by_role('dialog').inner_text()
                    页面.keyboard.press('Escape')
                    load_fixture(页面, 地址, self._样本('populated'), '满建-' + 后缀)
                    设置地图视角(页面, 'overview')
                    self._画面(页面, 'populated-' + 后缀)
                    设置地图视角(页面, 'follow')
                    self._画面(页面, 'closeup-' + 后缀)
                    上下文.close()
                浏览器.close()
            assert not self.错误, self.错误
            (self.输出 / 'report.json').write_text(json.dumps({'results': self.报告, 'errors': self.错误, 'physicalPhone': False}, ensure_ascii=False, indent=2))
            print('[完成] 青柠联排双视口、减少动态、混级补建、一次收租与存档验收通过。')
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    联排验收_类().api_执行()

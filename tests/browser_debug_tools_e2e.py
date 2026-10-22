"""通过生产页面、真实 Worker 和公开存档入口验收全地图调试工具。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import hashlib
import json
import os
import re
import subprocess

from playwright.sync_api import (
    Browser,
    ConsoleMessage,
    Dialog,
    Error,
    Page,
    Worker,
    expect,
    sync_playwright,
)
from browser_live_e2e import Handler, open_new_game_setup, select_map
from browser_main_game_acceptance import export_current, open_panel


# ◕ 功能
class 调试工具验收_类:
    """以实际导出的完整 GameState 检查界面调试结果与纯规则结果。

    更新日志：
    2026.10.22 - 建立六图双真人、现金草稿、非法输入、后台模拟及手机离线验收。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/debug-tools')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.控制台: list[dict] = []
        self.结果: list[dict] = []
        self.失败: list[dict] = []
        self.Worker地址: list[str] = []
        self.当前场景 = ''

    def _控制台消息(self, arg_消息: ConsoleMessage) -> None:
        self.控制台.append({'场景': self.当前场景, '类型': arg_消息.type, '消息': arg_消息.text})
        if arg_消息.type == 'error':
            self.错误.append(arg_消息.text)

    def _页面错误(self, arg_错误: Error) -> None:
        self.错误.append(str(arg_错误))

    def _对话(self, arg_对话: Dialog) -> None:
        arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None)

    def _Worker出现(self, arg_Worker: Worker) -> None:
        self.Worker地址.append(arg_Worker.url)

    def _期望模拟(self, arg_局面: dict, arg_轮数: int) -> dict:
        代码 = """
import fs from 'node:fs';
import {simulateDebugRounds} from './.test-dist/core/debug-tools.js';
const {game,rounds}=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(simulateDebugRounds(game,rounds).state));
"""
        return json.loads(subprocess.check_output(
            ['node', '--input-type=module', '-e', 代码],
            input=json.dumps({'game': arg_局面, 'rounds': arg_轮数}),
            text=True,
        ))

    def _导出(self, arg_页面: Page, arg_名称: str) -> dict:
        局面, 原文 = export_current(arg_页面)
        (self.输出 / (arg_名称 + '.json')).write_bytes(原文)
        return 局面

    def _等待画面(self, arg_页面: Page) -> None:
        arg_页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
        expect(arg_页面.locator('main.app-shell')).to_have_attribute('data-presenting', 'false')

    def _截图(self, arg_页面: Page, arg_名称: str) -> None:
        arg_页面.screenshot(path=str(self.输出 / (arg_名称 + '.png')))

    def _现金与非法输入(self, arg_页面: Page, arg_标识: str) -> dict:
        原局面 = self._导出(arg_页面, arg_标识 + '-initial')
        open_panel(arg_页面, '调试工具')
        第一行 = arg_页面.locator('.debug-cash-row').nth(0)
        第二行 = arg_页面.locator('.debug-cash-row').nth(1)
        第一行.locator('input').fill('24000')
        第二行.locator('input').fill('36000')
        第一行.get_by_role('button', name='设置', exact=True).click()
        expect(第二行.locator('input')).to_have_value('36000')
        第二行.get_by_role('button', name='设置', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('36,000')
        self._截图(arg_页面, arg_标识 + '-cash-panel')
        已设置 = self._导出(arg_页面, arg_标识 + '-cash')
        期望 = json.loads(json.dumps(原局面))
        期望['players'][0]['cash'] = 24000
        期望['players'][1]['cash'] = 36000
        assert 已设置 == 期望, '现金工具改变了现金以外的局面'
        open_panel(arg_页面, '调试工具')
        for 非法值 in ['-1', '1.5', '不是金额']:
            arg_页面.locator('.debug-cash-row input').first.fill(非法值)
            arg_页面.locator('.debug-cash-row').first.get_by_role('button', name='设置', exact=True).click()
            expect(arg_页面.locator('.debug-result')).to_contain_text('请输入')
        arg_页面.get_by_label('推进轮数').fill('0')
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('请输入')
        未修改 = self._导出(arg_页面, arg_标识 + '-invalid-unchanged')
        assert 未修改 == 已设置, '非法输入改变了真实存档'
        return 已设置

    def _模拟(
        self,
        arg_页面: Page,
        arg_原局面: dict,
        arg_轮数: int,
        arg_标识: str,
    ) -> dict:
        open_panel(arg_页面, '调试工具')
        arg_页面.get_by_label('推进轮数').fill(str(arg_轮数))
        # 只观察公开 DOM 的演出标记，避免借助 React 状态或隐藏入口伪造验收。
        arg_页面.evaluate("""() => {
          window.__debugPresentation = [];
          const record = () => {
            const main = document.querySelector('main.app-shell');
            window.__debugPresentation.push({
              presenting: main.dataset.presenting,
              step: main.dataset.sceneStep,
              dieActor: main.dataset.dieActor,
              construction: document.querySelector('.canvas-shell')?.dataset.constructionTiles ?? null,
            });
          };
          record();
          window.__debugObserver = new MutationObserver(record);
          window.__debugObserver.observe(document.querySelector('main.app-shell'), {
            attributes: true, subtree: true,
            attributeFilter: ['data-presenting','data-scene-step','data-die-actor','data-construction-tiles'],
          });
        }""")
        Worker数 = len(self.Worker地址)
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('模拟完成', timeout=30000)
        self._等待画面(arg_页面)
        assert len(self.Worker地址) > Worker数, '没有创建真实浏览器 Worker'
        assert 'debug-simulation' in self.Worker地址[-1]
        采样 = arg_页面.evaluate('() => { window.__debugObserver.disconnect(); return window.__debugPresentation; }')
        assert all(项['presenting'] == 'false' and 项['step'] == '0' and 项['dieActor'] == '' for 项 in 采样), 采样
        if arg_原局面['map']['id'] == 'lime-garden-30':
            expect(arg_页面.locator('.canvas-shell')).to_have_attribute('data-construction-tiles', '')
            assert all(项['construction'] in [None, ''] for 项 in 采样), 采样
        实际 = self._导出(arg_页面, arg_标识 + '-simulated')
        期望 = self._期望模拟(arg_原局面, arg_轮数)
        (self.输出 / (arg_标识 + '-expected.json')).write_text(json.dumps(期望, ensure_ascii=False, indent=2))
        assert 实际 == 期望, '界面 Worker 结果与完整规则模拟局面不相等'
        assert 实际['round'] == arg_原局面['round'] + arg_轮数
        self._截图(arg_页面, arg_标识 + '-world')
        return 实际

    def _继续操作(self, arg_页面: Page, arg_标识: str) -> None:
        arg_页面.get_by_role('button', name='我已就位，开始操作', exact=True).click()
        arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
        arg_页面.wait_for_function("document.querySelector('main').dataset.gamePhase !== 'await_roll'")
        self._等待画面(arg_页面)
        if arg_页面.locator('main').get_attribute('data-game-phase') == 'await_decision':
            arg_页面.get_by_role('button', name='暂不购买', exact=True).click()
        if arg_页面.locator('main').get_attribute('data-game-phase') == 'await_shop':
            arg_页面.get_by_role('button', name='离开商店', exact=True).click()
        暂不建设 = arg_页面.get_by_role('button', name='暂不建设', exact=True)
        if 暂不建设.count():
            暂不建设.click()
        else:
            arg_页面.get_by_role('button', name=re.compile('^结束当前回合')).click()
        arg_页面.get_by_role('button', name='我已就位，开始操作', exact=True).click()
        arg_页面.get_by_role('button', name=re.compile('^掷骰前进')).click()
        arg_页面.wait_for_function("document.querySelector('main').dataset.gamePhase !== 'await_roll'")
        self._等待画面(arg_页面)
        继续局面 = self._导出(arg_页面, arg_标识 + '-continued')
        最近掷骰 = [项 for 项 in 继续局面['events'] if 项['type'] == 'die_rolled'][-2:]
        assert [项['actorId'] for 项 in 最近掷骰] == ['p1', 'p2']

    def _验收地图(
        self,
        arg_浏览器: Browser,
        arg_地址: str,
        arg_地图: str,
        arg_手机: bool,
        arg_轮数: int,
    ) -> None:
        标识 = arg_地图 + ('-phone' if arg_手机 else '-desktop')
        self.当前场景 = 标识
        上下文 = arg_浏览器.new_context(
            viewport={'width': 390 if arg_手机 else 1440, 'height': 844 if arg_手机 else 900},
            accept_downloads=True,
            service_workers='allow',
        )
        页面 = 上下文.new_page()
        页面.on('console', self._控制台消息)
        页面.on('pageerror', self._页面错误)
        页面.on('dialog', self._对话)
        页面.on('worker', self._Worker出现)
        try:
            页面.goto(arg_地址)
            open_new_game_setup(页面)
            assert 页面.locator('.setup-map-choice button').count() == 6
            select_map(页面, arg_地图)
            页面.get_by_label('第 1 位玩家姓名').fill('玩家')
            页面.get_by_label('第 2 位玩家姓名').fill('对手')
            页面.get_by_label('第 2 位玩家类型').select_option('human')
            页面.get_by_label('对局种子').fill('17')
            页面.get_by_label('最多轮数').fill('20')
            页面.get_by_role('button', name='开始游戏', exact=True).click()
            self._等待画面(页面)
            已设置 = self._现金与非法输入(页面, 标识)
            实际 = self._模拟(页面, 已设置, arg_轮数, 标识)
            if arg_手机:
                页面.evaluate('async () => { await navigator.serviceWorker.ready; }')
                页面.wait_for_function('navigator.serviceWorker.controller !== null')
                已缓存 = 页面.evaluate("""async () => {
                  const keys = await caches.keys();
                  const urls = (await Promise.all(keys.map(async key => (await (await caches.open(key)).keys()).map(req => req.url)))).flat();
                  return urls.some(url => url.includes('debug-simulation.worker'));
                }""")
                assert 已缓存, 'PWA 未缓存实际调试 Worker'
                上下文.set_offline(True)
                实际 = self._模拟(页面, 实际, 1, 标识 + '-offline')
                self._截图(页面, 标识 + '-offline')
                上下文.set_offline(False)
            self._继续操作(页面, 标识)
            self.结果.append({
                '地图': arg_地图, '手机视口': arg_手机,
                '现金草稿保留': True, '非法输入不变': True, '实际Worker': True,
                '完整GameState相等': True, '轮数': arg_轮数,
                '结束轮次': 实际['round'], '关闭后掷骰交接': True,
                '离线Worker': arg_手机, '历史演出为空': True,
                '最终状态SHA256': hashlib.sha256(json.dumps(实际, sort_keys=True).encode()).hexdigest(),
            })
            print('[完成] 调试工具真实浏览器验收：' + 标识, flush=True)
        except BaseException as 错误:
            self.失败.append({'场景': 标识, '原因': str(错误)})
            self._截图(页面, 标识 + '-failure')
            raise
        finally:
            上下文.close()

    def api_执行(self) -> None:
        日志 = Path('/tmp/depth-debug-tests.log').read_text()
        assert re.search(r'# tests \d+', 日志), '等待主 Agent 完成实际生产构建与测试，禁止另行构建'
        地图 = json.loads(Path('src/data/levels.json').read_text())['levels']
        可选地图 = [项['map']['id'] for 项 in 地图 if 项['playable']]
        assert len(可选地图) == 6
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        地址 = f'http://127.0.0.1:{服务.server_port}/ReactMono/'
        try:
            with sync_playwright() as 工具:
                参数 = {'headless': True, 'args': ['--no-sandbox', '--disable-dev-shm-usage']}
                if 'CHROMIUM_PATH' in os.environ:
                    参数['executable_path'] = os.environ['CHROMIUM_PATH']
                else:
                    参数['channel'] = 'chrome'
                浏览器 = 工具.chromium.launch(**参数)
                try:
                    for 索引, 地图标识 in enumerate(可选地图):
                        self._验收地图(浏览器, 地址, 地图标识, False, 索引 % 3 + 1)
                    self._验收地图(浏览器, 地址, 'lime-garden-30', True, 2)
                finally:
                    浏览器.close()
            assert not self.错误, self.错误
        finally:
            (self.输出 / 'browser-report.json').write_text(json.dumps({
                '结果': self.结果, '失败': self.失败, '错误': self.错误, '控制台': self.控制台,
                'Worker地址': self.Worker地址, '物理手机': False,
            }, ensure_ascii=False, indent=2))
            服务.shutdown()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    调试工具验收_类().api_执行()

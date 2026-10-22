"""从真实输入、后台 Worker 和文件存档验证长局经营。"""

# ◑ 导入
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import subprocess

from playwright.sync_api import Page, expect, sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map
from browser_main_game_acceptance import (
    设置地图视角,
    export_current,
    fixture,
    load_fixture,
    open_panel,
)


# ◕ 功能
class 长局经营验收_类:
    """真实复现截图操作并检查输入没有被忽略。

    更新日志：
    2026.10.22 - 覆盖默认破产决胜、未提交金额、200轮、取消和旧局切换。
    """

    def __init__(self) -> None:
        self.输出 = Path('artifacts/long-economy')
        self.输出.mkdir(parents=True, exist_ok=True)
        self.错误: list[str] = []
        self.结果: list[dict] = []

    def _期望(self, arg_局面: dict) -> dict:
        代码 = """
import fs from 'node:fs';
import {prepareDebugSimulation,simulateDebugRounds} from './.test-dist/core/debug-tools.js';
const game=JSON.parse(fs.readFileSync(0,'utf8'));
const prepared=prepareDebugSimulation(game,{cashById:{p1:1000000,p2:1000000},endCondition:'bankruptcy'});
console.log(JSON.stringify(simulateDebugRounds(prepared,200).state));
"""
        return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', 代码], input=json.dumps(arg_局面), text=True))

    def _百万长局(self, arg_页面: Page) -> None:
        open_new_game_setup(arg_页面)
        select_map(arg_页面, 'lime-garden-30')
        assert arg_页面.get_by_label('对局结束方式', exact=True).count() == 1, '新局缺少明确的破产决胜选择'
        expect(arg_页面.get_by_label('对局结束方式', exact=True)).to_have_value('bankruptcy')
        arg_页面.get_by_role('button', name='开始游戏', exact=True).click()
        arg_页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
        原局, _ = export_current(arg_页面)
        assert 原局['endCondition'] == 'bankruptcy'
        assert '/ 36' not in arg_页面.locator('.round-indicator').inner_text()
        open_panel(arg_页面, '调试工具')
        # 延迟投递仍使用真实 Worker，使取消测试不会与小样本计算速度争抢。
        arg_页面.evaluate("""() => {
          window.__workerPosts=0;
          const post=Worker.prototype.postMessage;
          Worker.prototype.postMessage=function(...args){
            window.__workerPosts++;
            const delay=window.__delayDebugPost ? 1500 : 0;
            setTimeout(()=>post.apply(this,args),delay);
          };
        }""")
        输入 = arg_页面.locator('.debug-cash-row input')
        输入.nth(0).fill('1000000')
        输入.nth(1).fill('-1')
        arg_页面.get_by_label('推进轮数', exact=True).fill('200')
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('请输入')
        assert arg_页面.evaluate('window.__workerPosts') == 0
        输入.nth(1).fill('1000000')
        arg_页面.evaluate('window.__delayDebugPost=true')
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        arg_页面.get_by_role('button', name='取消模拟', exact=True).click()
        arg_页面.wait_for_timeout(1700)
        取消局, _ = export_current(arg_页面)
        assert 取消局 == 原局, '取消模拟时金额草稿已经污染真实对局'
        open_panel(arg_页面, '调试工具')
        arg_页面.evaluate('window.__delayDebugPost=false')
        for 序号 in [0, 1]:
            arg_页面.locator('.debug-cash-row input').nth(序号).fill('1000000')
        arg_页面.get_by_label('推进轮数', exact=True).fill('10000')
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('模拟失败', timeout=30000)
        expect(arg_页面.locator('.debug-result')).to_contain_text('上限')
        失败局, _ = export_current(arg_页面)
        assert 失败局 == 原局, '真实Worker失败后资金草稿被部分应用'
        open_panel(arg_页面, '调试工具')
        输入 = arg_页面.locator('.debug-cash-row input')
        for 序号 in [0, 1]:
            输入.nth(序号).fill('1000000')
        arg_页面.get_by_label('推进轮数', exact=True).fill('200')
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('模拟完成', timeout=30000)
        arg_页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
        实际, 原文 = export_current(arg_页面)
        assert 实际 == self._期望(原局), '真实Worker未采用输入的百万资金或结束方式'
        assert 实际['status'] == 'playing' and 实际['round'] == 201
        assert all(玩家['cash'] + 玩家['bankBalance'] > 900000 for 玩家 in 实际['players'])
        产权数 = len([地块 for 地块 in 实际['tiles'] if 地块['ownerId']])
        房屋数 = len([地块 for 地块 in 实际['tiles'] if 地块['ownerId'] and 地块['level'] > 0])
        assert 产权数 >= 20 and 房屋数 >= 18
        assert all(事件['details']['amount'] <= 事件['details']['due'] for 事件 in 实际['events'] if 事件['type'] == 'rent_paid')
        标识 = 'phone' if arg_页面.viewport_size['width'] < 600 else 'desktop'
        (self.输出 / f'long-{标识}.json').write_bytes(原文)
        设置地图视角(arg_页面, 'overview')
        arg_页面.wait_for_timeout(700)
        arg_页面.screenshot(path=str(self.输出 / f'long-{标识}.png'))
        arg_页面.wait_for_function('navigator.serviceWorker.controller !== null')
        arg_页面.context.set_offline(True)
        arg_页面.reload(wait_until='load')
        arg_页面.get_by_role('button', name='继续游戏').click()
        arg_页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
        重载, _ = export_current(arg_页面)
        assert 重载 == 实际
        arg_页面.context.set_offline(False)
        self.结果.append({'viewport': 标识, 'round': 实际['round'], 'properties': 产权数, 'houses': 房屋数, 'draftApplied': True, 'cancelUnchanged': True, 'workerFailureUnchanged': True, 'invalidAtomic': True, 'offlineRestored': True})

    def _旧局切换(self, arg_页面: Page) -> None:
        原文 = fixture("game=act(createGame(17,{...cfg,maxRounds:1,specialEnabled:false}),'start_game');")
        load_fixture(arg_页面, arg_页面.url, 原文, '旧限轮对局')
        open_panel(arg_页面, '调试工具')
        expect(arg_页面.get_by_label('模拟结束方式', exact=True)).to_have_value('round_limit')
        arg_页面.get_by_label('模拟结束方式', exact=True).select_option('bankruptcy')
        for 序号 in [0, 1]:
            arg_页面.locator('.debug-cash-row input').nth(序号).fill('1000000')
        arg_页面.get_by_label('推进轮数', exact=True).fill('10')
        arg_页面.get_by_role('button', name='一键模拟', exact=True).click()
        expect(arg_页面.locator('.debug-result')).to_contain_text('模拟完成', timeout=30000)
        arg_页面.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=60000)
        实际, _ = export_current(arg_页面)
        assert 实际['endCondition'] == 'bankruptcy'
        assert 实际['round'] == 11 and 实际['status'] == 'playing'
        self.结果[-1]['legacyModeSwitched'] = True

    def api_执行(self) -> None:
        服务 = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        线程 = Thread(target=服务.serve_forever, daemon=True)
        线程.start()
        try:
            with sync_playwright() as 工具:
                浏览器 = 工具.chromium.launch(channel='chrome', headless=True)
                for 手机 in [False, True]:
                    上下文 = 浏览器.new_context(viewport={'width': 390 if 手机 else 1440, 'height': 844 if 手机 else 900}, reduced_motion='reduce', accept_downloads=True, service_workers='allow')
                    页面 = 上下文.new_page()
                    页面.on('pageerror', lambda arg_错: self.错误.append(str(arg_错)))
                    页面.on('dialog', lambda arg_对话: arg_对话.accept('当前验收' if arg_对话.type == 'prompt' else None))
                    页面.goto(f'http://127.0.0.1:{服务.server_port}/ReactMono/')
                    self._百万长局(页面)
                    self._旧局切换(页面)
                    上下文.close()
                浏览器.close()
            assert not self.错误, self.错误
            (self.输出 / 'browser-report.json').write_text(json.dumps({'results': self.结果, 'errors': self.错误, 'physicalPhone': False}, ensure_ascii=False, indent=2))
        finally:
            服务.shutdown()
            服务.server_close()
            线程.join()


# ◍ 运行
if __name__ == '__main__':
    长局经营验收_类().api_执行()

"""主程序新版标题、准备、HUD、演出屏障与本机继续游戏浏览器验收。"""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup
import re, os

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            opts={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
            if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
            else:opts['channel']='chrome'
            browser=p.chromium.launch(**opts)
            for width,height in [(1440,900),(390,844)]:
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='no-preference',service_workers='allow')
                page=context.new_page();errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('dialog',lambda dialog:dialog.accept())
                page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/',wait_until='load')
                assert page.locator('.title-shell').count()==1
                assert page.locator('canvas').count()==0
                assert page.get_by_role('heading',name='大富翁').count()==1
                open_new_game_setup(page)
                assert page.locator('canvas').count()==0
                page.get_by_label('玩家人数').select_option('2')
                page.get_by_label('对局种子').fill('17')
                page.get_by_label('最多轮数').fill('3')
                page.get_by_role('button',name='开始游戏').click()
                page.locator('main.app-shell').wait_for()
                page.locator('.canvas-shell[data-ready="true"]').wait_for(timeout=15000)
                assert page.locator('canvas').count()==1
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
                page.get_by_role('button',name='掷骰前进').click()
                page.wait_for_timeout(150)
                assert page.locator('.purchase-actions').count()==0
                page.locator('.purchase-actions').wait_for(timeout=8000)
                assert page.locator('main').get_attribute('data-game-phase')=='await_decision'
                assert '1 点' in page.locator('.scene-hud').inner_text()
                page.get_by_role('button',name=re.compile('购买地产')).click()
                assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
                assert '1 点' in page.locator('.scene-hud').inner_text()
                page.locator('.finance-tabs').get_by_role('button',name='银行').click()
                assert page.locator('#bank-actions').is_visible()
                page.keyboard.press('Escape')
                assert page.locator('.turn-card').get_attribute('data-panel-open')=='false'
                page.locator('.utility-menu>summary').click()
                page.locator('.utility-menu-items>.tile-semantic-list>summary').click()
                assert page.locator('.tile-semantic-list[open]').count()==1
                page.keyboard.press('Escape')
                assert page.locator('.tile-semantic-list[open]').count()==0
                page.wait_for_timeout(500)
                page.get_by_role('button',name='返回标题').click()
                page.locator('.title-shell').wait_for()
                page.get_by_role('button',name='继续游戏').wait_for(timeout=8000)
                page.get_by_role('button',name='继续游戏').click()
                page.locator('main.app-shell').wait_for()
                assert page.locator('main').get_attribute('data-game-phase')=='await_end_turn'
                assert not errors,errors
                print(f'PASS title/setup/game/save flow at {width}×{height}; no page errors or horizontal overflow')
                context.close()
            browser.close()
    finally:
        server.shutdown();thread.join()

if __name__=='__main__':main()

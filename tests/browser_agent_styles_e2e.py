"""#42: real Chromium strategy selection, autoplay, local save and mobile screenshots."""
from pathlib import Path
from threading import Thread
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import re

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    screenshots=Path('artifacts/issue42')
    screenshots.mkdir(parents=True,exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            errors=[]
            context=browser.new_context(viewport={'width':1366,'height':900},service_workers='allow')
            page=context.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.accept('电脑策略存档' if d.type=='prompt' else None))
            url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
            page.goto(url)
            page.get_by_label('第 1 位玩家类型').select_option('computer')
            page.get_by_label('第 1 位电脑策略').select_option('conservative')
            page.get_by_label('第 2 位电脑策略').select_option('aggressive')
            page.get_by_label('游戏地图').select_option('harbor-20')
            page.get_by_label('最多轮数').fill('3')
            page.get_by_label('启用医院、监狱与商店').check()
            page.get_by_label('快速模式').check()
            page.screenshot(path=str(screenshots/'desktop-setup.png'),full_page=True)
            assert page.get_by_label('第 1 位电脑策略').input_value()=='conservative'
            assert page.get_by_label('第 2 位电脑策略').input_value()=='aggressive'
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='finished'",timeout=30000)
            page.screenshot(path=str(screenshots/'desktop-finished.png'),full_page=True)
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list li').filter(has_text='电脑策略存档').wait_for()
            page.get_by_role('button',name=re.compile('重新开局')).click()
            page.locator('.save-list li').filter(has_text='电脑策略存档').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='finished'",timeout=15000)
            assert page.locator('main').get_attribute('data-game-status')=='finished'
            assert page.get_by_text('电脑策略存档').count()>0
            context.close()
            mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,
                device_scale_factor=1,service_workers='allow')
            phone=mobile.new_page()
            phone.on('pageerror',lambda e:errors.append(str(e)))
            phone.goto(url)
            phone.get_by_label('第 2 位电脑策略').select_option('balanced')
            phone.screenshot(path=str(screenshots/'mobile-setup.png'),full_page=True)
            phone.get_by_role('button',name=re.compile('开始游戏')).click()
            assert phone.locator('main').get_attribute('data-game-status')=='playing'
            assert not errors,errors
            print('PASS #42 Chromium: three styles, full autoplay, save/restore, mobile touch setup; 3 screenshots')
            browser.close()
    finally:
        server.shutdown()
        thread.join()

if __name__=='__main__':
    run()

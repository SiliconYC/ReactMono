"""#40: real Chrome offline PWA actions, UI card acquisition, use and IndexedDB resume."""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
import re

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=browser.new_context(service_workers='allow',accept_downloads=True)
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda dialog:dialog.accept('策略卡离线' if dialog.type=='prompt' else None))
            url=f'http://127.0.0.1:{server.server_port}/ReactMono/'
            page.goto(url)
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            context.set_offline(True)
            for seed,kind,button in [(263,'遥控骰子','使用遥控骰子'),(60,'路障','放置路障'),(257,'免租卡','使用免租卡')]:
                page.goto(url)
                assert '已断网' in page.locator('.network-indicator').inner_text()
                page.get_by_label('对局种子').fill(str(seed))
                page.get_by_label('快速模式').check()
                page.get_by_role('button',name=re.compile('开始游戏')).click()
                page.get_by_role('button',name=re.compile('掷骰前进')).click()
                assert kind in page.locator('.activity-card').inner_text(),(seed,page.locator('.activity-card').inner_text())
                page.get_by_role('button',name='结束当前回合').click()
                page.get_by_role('button',name=re.compile(button)).wait_for(timeout=25000)
                if kind=='遥控骰子':
                    page.get_by_label('遥控骰点').select_option('4')
                    page.get_by_role('button',name=button).click()
                    assert '指定骰点 4' in page.locator('.activity-card').inner_text()
                    page.get_by_role('button',name=re.compile('掷骰前进')).click()
                    assert '掷出 4 点' in page.locator('.activity-card').inner_text()
                elif kind=='路障':
                    target=page.get_by_label('路障目标格').input_value()
                    assert int(target)>0
                    page.get_by_role('button',name=button).click()
                    assert '🚧' in page.locator('.tile-index').all_inner_texts().__str__()
                    page.get_by_role('button',name='创建手动存档').click()
                    slot=page.locator('.save-list li').filter(has_text='策略卡离线')
                    slot.wait_for()
                    page.reload(wait_until='load')
                    slot=page.locator('.save-list li').filter(has_text='策略卡离线')
                    slot.get_by_role('button',name='读取').click()
                    assert '🚧' in ''.join(page.locator('.tile-index').all_inner_texts())
                    assert page.locator('main').get_attribute('data-game-phase')=='await_roll'
                else:
                    page.get_by_role('button',name=button).click()
                    assert '本次免租' in page.locator('.purchase-info').inner_text()
                    page.get_by_role('button',name=re.compile('掷骰前进')).click()
                    assert '本次免租' not in page.locator('.purchase-info').all_inner_texts().__str__()
            assert not errors,errors
            print('PASS: Chromium offline strategy cards acquired and operated, roadblock preserved after IndexedDB reload')
            browser.close()
    finally:
        server.shutdown();thread.join()
if __name__=='__main__':run()

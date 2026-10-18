"""P3-07 true Chromium: offline bank transfers, save and restore, no actor leaks."""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler, open_new_game_setup, select_map
import re

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=browser.new_context(viewport={'width':390,'height':844},service_workers='allow')
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.accept('银行验收' if d.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            open_new_game_setup(page)
            page.evaluate("navigator.serviceWorker.ready.then(()=>true)")
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            context.set_offline(True)
            page.reload(wait_until='load')
            assert '已断网' in page.locator('.network-indicator').inner_text()
            page.get_by_label('对局种子').fill('17')
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            found=page.evaluate("""async()=>{
              const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(b){b.click();return true}return false};
              for(let i=0;i<100;i++){
                if(document.querySelector('.bank-actions'))return true;
                if(!click('掷骰前进')&&!click('购买地产'))click('放弃购买');
                await new Promise(r=>setTimeout(r,20));
              }
              return false;
            }""")
            assert found,'Cannot reach bank phase'
            page.get_by_role('button',name='银行',exact=True).click()
            def balances():
                s=page.locator('.turn-position').inner_text()
                a=re.search(r'资金：\s*([0-9,]+)',s)
                b=re.search(r'银行存款：\s*([0-9,]+)',s)
                assert a and b,s
                return int(a.group(1).replace(',','')),int(b.group(1).replace(',',''))
            initial=balances()
            page.get_by_label('银行交易金额').fill('200')
            page.get_by_role('button',name='存入银行').click()
            assert balances()==(initial[0]-200,initial[1]+200),(initial,balances())
            page.get_by_label('银行交易金额').fill('75')
            page.get_by_role('button',name='从银行取款').click()
            saved=balances()
            assert saved==(initial[0]-125,initial[1]+125)
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list').get_by_text('银行验收').wait_for()
            page.reload()
            page.locator('.save-list').get_by_text('银行验收').wait_for()
            page.locator('.save-list li').filter(has_text='银行验收').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gamePhase==='await_end_turn'")
            assert balances()==saved,(saved,balances())
            assert page.locator('main').get_attribute('data-game-status')=='playing'
            assert not errors,errors
            print('PASS: offline bank deposit/withdraw, balanced ledger, IndexedDB save/reload/restore',saved)
            browser.close()
    finally:
        server.shutdown();thread.join()
if __name__=='__main__':run()

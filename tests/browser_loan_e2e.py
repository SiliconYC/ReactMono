"""P3-08: Chromium + offline mortgage, borrow/repay and save restore."""
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
            context=browser.new_context(viewport={'width':440,'height':880},service_workers='allow')
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.accept('贷款验收' if d.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            context.set_offline(True);page.reload(wait_until='load')
            assert '已断网' in page.locator('.network-indicator').inner_text()
            page.get_by_label('对局种子').fill('17')
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            found=page.evaluate("""async()=>{
              const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
              for(let i=0;i<100;i++){
                if(document.querySelector('.loan-actions button')?.textContent.includes('抵押'))return true;
                if(!click('掷骰前进')&&!click('购买地产'))click('放弃购买');
                await new Promise(r=>setTimeout(r,20));
              }
              return false;
            }""")
            assert found,'No mortgage-eligible property appeared'
            page.get_by_role('button',name='抵押借贷',exact=True).click()
            cash_before=page.locator('.turn-position').inner_text()
            page.locator('#loan-actions').get_by_role('button',name=re.compile('^抵押')).first.click()
            page.get_by_label('银行交易金额').fill('20')
            page.get_by_role('button',name='借入贷款').click()
            assert '贷款：' in page.locator('.turn-position').inner_text()
            assert '20' in page.locator('.loan-actions').inner_text()
            page.get_by_role('button',name='偿还贷款').click()
            assert '贷款 0' in page.locator('.loan-actions').inner_text()
            page.get_by_role('button',name=re.compile('解除抵押')).first.click()
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list').get_by_text('贷款验收').wait_for()
            page.reload()
            page.locator('.save-list li').filter(has_text='贷款验收').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gamePhase==='await_end_turn'")
            page.get_by_role('button',name='抵押借贷',exact=True).click()
            assert '贷款 0' in page.locator('.loan-actions').inner_text()
            assert '20' not in page.locator('.turn-position').inner_text().split('贷款：')[-1].split('·')[0]
            assert not errors,errors
            print('PASS: offline mortgage/loan/redeem and IndexedDB restore',cash_before)
            browser.close()
    finally:
        server.shutdown();thread.join()

if __name__=='__main__':run()

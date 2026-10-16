"""P3-06 Chromium: real sale button, confirmation, accounting and save/reload."""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_local_multiplayer_e2e import Handler
import re

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            page=browser.new_page(viewport={'width':390,'height':844})
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('最多轮数').fill('40')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            found=page.evaluate("""async()=>{
              const wait=()=>new Promise(r=>setTimeout(r,16));
              const click=s=>{const x=[...document.querySelectorAll('button')].find(b=>b.textContent.includes(s)&&!b.disabled);if(x){x.click();return true}return false};
              for(let i=0;i<1500;i++){
                const sale=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('出售 ')&&!b.disabled);
                if(sale)return {ready:true,label:sale.textContent.trim()};
                if(document.querySelector('main')?.dataset.gameStatus==='finished')break;
                if(click('掷骰前进')){}
                else if(click('购买地产')){}
                else if(click('放弃购买')){}
                else if(click('结束当前回合')){}
                await wait();
              }
              return {ready:false};
            }""")
            assert found['ready'],found
            before=page.locator('.turn-position').inner_text()
            buttons=page.get_by_role('button',name=re.compile('出售 '))
            assert buttons.count()>0
            sale=buttons.first
            label=sale.inner_text()
            value=int(re.search(r'回收\s*(\d+)',label).group(1))
            numeric=lambda t:int(re.search(r'资金：\s*([\d,]+)',t).group(1).replace(',',''))
            old=numeric(before)
            page.on('dialog',lambda dialog:dialog.accept('出售测试' if dialog.type=='prompt' else None))
            sale.click()
            page.wait_for_function("document.querySelector('.turn-tip')?.textContent.includes('出售')")
            after=numeric(page.locator('.turn-position').inner_text())
            assert after-old==value,(old,after,value)
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list li').filter(has_text='出售测试').wait_for()
            page.reload()
            page.locator('.save-list li').filter(has_text='出售测试').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
            assert numeric(page.locator('.turn-position').inner_text())==after
            assert not errors,errors
            print('PASS: confirmed sale + real mobile balance + reload persistence',value)
            browser.close()
    finally:
        server.shutdown();worker.join()

if __name__=='__main__':main()

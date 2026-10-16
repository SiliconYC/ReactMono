"""断网后真实 Chromium 从 Service Worker 本地缓存启动、续档并玩完整局。"""
from http.server import ThreadingHTTPServer
from threading import Thread
import re
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
            context=browser.new_context(service_workers='allow')
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda dialog:dialog.accept('离线存档' if dialog.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.evaluate("navigator.serviceWorker.ready.then(()=>true)")
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            scope=page.evaluate("navigator.serviceWorker.controller.scriptURL")
            assert scope.endswith('/ReactMono/sw.js'),scope
            context.set_offline(True)
            page.reload(wait_until='load')
            assert page.locator('.tile').count()==24
            assert '已断网' in page.locator('.network-indicator').inner_text()
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list').get_by_text('离线存档').wait_for()
            page.reload()
            page.locator('.save-list').get_by_text('离线存档').wait_for()
            page.locator('.save-list li').filter(has_text='离线存档').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
            result=page.evaluate("""async()=>{
                const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
                const pause=()=>new Promise(r=>setTimeout(r,12));
                let rolls=0;
                // Automatic property liquidation extends legitimate games; never stop before the full 60-round limit.
                for(let i=0;i<7000;i++){
                    if(document.querySelector('main[data-game-status]')?.dataset.gameStatus==='finished')return {finished:true,rolls};
                    if(click('掷骰前进'))rolls++;
                    else if(click('购买地产')){}
                    else if(click('放弃购买')){}
                    else if(click('结束当前回合')){}
                    await pause();
                }
                return {finished:false,rolls};
            }""")
            assert result['finished'] and result['rolls']>0,result
            assert not errors,errors
            print('PASS: PWA HTTPS 等效 localhost scope；离线启动、IndexedDB 续档、完整对局',result)
            browser.close()
    finally:
        server.shutdown();thread.join()
if __name__=='__main__':main()

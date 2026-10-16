"""P3-10: Chrome, real offline share trades, quote movements and manual export/import."""
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler
from pathlib import Path
from tempfile import TemporaryDirectory
import re

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p, TemporaryDirectory() as folder:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            context=browser.new_context(viewport={'width':420,'height':880},service_workers='allow',accept_downloads=True)
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('dialog',lambda d:d.accept('股票验收' if d.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            context.set_offline(True)
            page.reload(wait_until='load')
            assert '已断网' in page.locator('.network-indicator').inner_text()
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            reached=page.evaluate("""async()=>{
              const click=t=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(t)&&!x.disabled);if(!b)return false;b.click();return true};
              for(let i=0;i<120;i++){
                if(document.querySelector('.stock-actions'))return true;
                if(!click('掷骰前进')&&!click('购买地产'))click('放弃购买');
                await new Promise(r=>setTimeout(r,20));
              }
              return false;
            }""")
            assert reached,'No trading phase'
            row=page.locator('.stock-entry').filter(has_text='青禾农业')
            initial_text=row.inner_text()
            assert '持有 0 股' in initial_text,initial_text
            page.get_by_label('股票交易数量').fill('2')
            page.get_by_role('button',name='买入 青禾农业').click()
            assert '持有 2 股' in row.inner_text()
            assert '手续费' in page.locator('.turn-tip').inner_text()
            page.get_by_role('button',name='创建手动存档').click()
            page.locator('.save-list li').filter(has_text='股票验收').wait_for()
            with page.expect_download() as info:
                page.locator('.save-list li').filter(has_text='股票验收').get_by_role('button',name='导出').click()
            target=str(Path(folder)/'stock-backup.json')
            info.value.save_as(target)
            saved_cash=page.locator('.turn-position').inner_text()
            page.reload(wait_until='load')
            slot=page.locator('.save-list li').filter(has_text='股票验收')
            slot.get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('.stock-actions')!==null")
            assert '持有 2 股' in page.locator('.stock-entry').filter(has_text='青禾农业').inner_text()
            assert page.locator('.turn-position').inner_text()==saved_cash
            # Let the opponents take their turns, triggering the seeded quote update.
            advance=page.evaluate("""async()=>{
              const click=t=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(t)&&!x.disabled);if(!b)return false;b.click();return true};
              for(let i=0;i<320;i++){
                const text=document.querySelector('.board-center-label')?.textContent||'';
                if(document.querySelector('.stock-actions')&&/第\s*[2-9]/.test(text))return true;
                if(!click('结束当前回合')&&!click('掷骰前进')&&!click('购买地产'))click('放弃购买');
                await new Promise(r=>setTimeout(r,25));
              }
              return false;
            }""")
            assert advance,'Market failed to advance to the next round'
            page.get_by_label('股票交易数量').fill('2')
            page.get_by_role('button',name='卖出 青禾农业').click()
            assert '持有 0 股' in page.locator('.stock-entry').filter(has_text='青禾农业').inner_text()
            assert '已实现盈亏' in page.locator('.turn-tip').inner_text()
            # Import the earlier live-position backup and verify market/lot restoration.
            page.get_by_label('导入 JSON 存档文件').set_input_files(target)
            page.get_by_role('region',name='存档导入预览').wait_for()
            page.get_by_role('button',name='另存为副本').click()
            restored=page.locator('.save-list li').filter(has_text='股票验收（副本）')
            restored.wait_for()
            restored.get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('.stock-actions')!==null")
            assert '持有 2 股' in page.locator('.stock-entry').filter(has_text='青禾农业').inner_text()
            assert page.locator('.turn-position').inner_text()==saved_cash
            assert not errors,errors
            print('PASS: genuine offline stock buy, round quote advance, sell, JSON export/import and restored positions')
            browser.close()
    finally:
        server.shutdown();thread.join()

if __name__=='__main__':run()

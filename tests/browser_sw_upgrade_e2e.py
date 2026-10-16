"""Chromium 真正安装两个 Service Worker 版本，验证明确更新后 IndexedDB 和离线入口不丢失。"""
from http.server import ThreadingHTTPServer
from threading import Thread
import re
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler,ROOT

class UpdateHandler(Handler):
    version=0
    def do_GET(self):
        if self.path.split('?')[0]=='/ReactMono/sw.js':
            sw=(ROOT/'dist/sw.js').read_text()
            if UpdateHandler.version:
                sw=re.sub(r'reactmono-[a-f0-9]{16}', 'reactmono-0123456789abcdef',sw)
            payload=sw.encode()
            self.send_response(200)
            self.send_header('Content-Type','application/javascript; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        return super().do_GET()

def main():
    UpdateHandler.version=0
    server=ThreadingHTTPServer(('127.0.0.1',0),UpdateHandler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
            context=browser.new_context(service_workers='allow')
            page=context.new_page()
            page.on('dialog',lambda d:d.accept('更新前备份' if d.type=='prompt' else None))
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            page.get_by_label('对局种子').fill('31')
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.get_by_role('button',name='创建手动存档').click()
            row=page.locator('.save-list li').filter(has_text='更新前备份')
            row.wait_for()
            previous=page.evaluate("navigator.serviceWorker.controller.scriptURL")
            assert previous.endswith('/ReactMono/sw.js')
            UpdateHandler.version=1
            page.evaluate("async()=>{const r=await navigator.serviceWorker.ready;await r.update()}")
            page.get_by_role('button',name='检测到新版，保存并更新').wait_for(timeout=12000)
            page.get_by_role('button',name='检测到新版，保存并更新').click()
            page.wait_for_load_state('load')
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            page.locator('.save-list li').filter(has_text='更新前备份').wait_for()
            assert page.locator('.tile').count()==24
            context.set_offline(True)
            page.reload()
            assert '已断网' in page.locator('.network-indicator').inner_text()
            page.locator('.save-list li').filter(has_text='更新前备份').get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('.save-message')?.textContent.includes('已读取「更新前备份」')")
            assert page.locator('main').get_attribute('data-game-status')=='playing'
            assert not errors,errors
            print('PASS: 新旧 Service Worker 缓存版本安装→确认更新→断网重启→既有存档读取')
            browser.close()
    finally:
        server.shutdown();thread.join()
if __name__=='__main__': main()

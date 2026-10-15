"""从真实文件下载和上传到 Chromium，验证备份及损坏拒绝。"""
from http.server import ThreadingHTTPServer
from threading import Thread
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
            page=browser.new_page(accept_downloads=True)
            errors=[]
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('dialog',lambda dialog:dialog.accept('备份样本' if dialog.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.get_by_label('对局种子').fill('17')
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            revision=page.locator('main').get_attribute('data-game-revision')
            page.get_by_role('button',name='创建手动存档').click()
            row=page.locator('.save-list li').filter(has_text='备份样本')
            row.wait_for()
            with page.expect_download() as download_info:
                row.get_by_role('button',name='导出').click()
            download=download_info.value
            contents=Path(download.path()).read_bytes()
            assert b'reactmono-save' in contents
            assert json.loads(contents)['game']['revision']==int(revision)
            row.get_by_role('button',name='删除').click()
            page.wait_for_function("!document.querySelector('.save-list')?.textContent.includes('备份样本')")
            selector=page.get_by_label('导入 JSON 存档文件')
            selector.set_input_files({'name':download.suggested_filename,'mimeType':'application/json','buffer':contents})
            page.get_by_role('region',name='存档导入预览').wait_for()
            assert page.get_by_label('导入存档名称').input_value()=='备份样本'
            page.get_by_role('button',name='确认导入存档').click()
            row=page.locator('.save-list li').filter(has_text='备份样本')
            row.wait_for()
            row.get_by_role('button',name='读取').click()
            page.wait_for_function('(revision)=>document.querySelector("main")?.dataset.gameRevision===revision',arg=revision)
            modified=json.loads(contents)
            modified['game']['randomState']=17
            selector.set_input_files({'name':'corrupted.json','mimeType':'application/json','buffer':json.dumps(modified,ensure_ascii=False).encode()})
            page.wait_for_function("document.querySelector('.save-message')?.textContent.includes('导入失败')")
            assert row.count()==1
            selector.set_input_files({'name':download.suggested_filename,'mimeType':'application/json','buffer':contents})
            page.get_by_role('button',name='另存为副本').click()
            page.locator('.save-list li').filter(has_text='备份样本（副本）').wait_for()
            assert not errors,errors
            print('PASS: 真实 JSON 下载、删除、导入续局、损坏拒绝、同名另存为副本')
            browser.close()
    finally:
        server.shutdown();thread.join()
if __name__=='__main__':main()

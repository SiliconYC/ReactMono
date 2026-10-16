"""P2 一条真实 Chromium 流程：联网安装→文件备份→删除导入→断网读档→卡片/升级→完整胜负。"""
from http.server import ThreadingHTTPServer
from threading import Thread
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
from browser_live_e2e import Handler

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
            context=browser.new_context(service_workers='allow',accept_downloads=True)
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('dialog',lambda d:d.accept('P2验收' if d.type=='prompt' else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/ReactMono/')
            page.wait_for_function("navigator.serviceWorker.controller!==null")
            assert page.locator('.tile').count()==24
            page.get_by_label('对局种子').fill('17')
            page.get_by_label('快速模式').check()
            page.get_by_role('button',name=re.compile('开始游戏')).click()
            page.get_by_role('button',name=re.compile('掷骰前进')).click()
            page.get_by_role('button',name='创建手动存档').click()
            row=page.locator('.save-list li').filter(has_text='P2验收')
            row.wait_for()
            with page.expect_download() as d:
                row.get_by_role('button',name='导出').click()
            data=Path(d.value.path()).read_bytes()
            assert b'reactmono-save' in data
            row.get_by_role('button',name='删除').click()
            page.wait_for_function("!document.querySelector('.save-list')?.textContent.includes('P2验收')")
            page.get_by_label('导入 JSON 存档文件').set_input_files(
                {'name':'p2-backup.json','mimeType':'application/json','buffer':data})
            page.get_by_role('region',name='存档导入预览').wait_for()
            page.get_by_label('导入存档名称').fill('P2验收')
            page.get_by_role('button',name='确认导入存档').click()
            row=page.locator('.save-list li').filter(has_text='P2验收')
            row.wait_for()
            context.set_offline(True)
            page.reload()
            assert '已断网' in page.locator('.network-indicator').inner_text()
            row=page.locator('.save-list li').filter(has_text='P2验收')
            row.wait_for()
            row.get_by_role('button',name='读取').click()
            page.wait_for_function("document.querySelector('main')?.dataset.gameStatus==='playing'")
            report=page.evaluate("""async()=>{
                const click=s=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.includes(s)&&!x.disabled);if(!b)return false;b.click();return true};
                const wait=()=>new Promise(r=>setTimeout(r,20));
                let rolls=0,upgrades=0,cards=0,sawEvent=false;
                for(let i=0;i<1800;i++){
                    let activity=document.querySelector('.activity-card')?.textContent||'';
                    if(activity.includes('事件格'))sawEvent=true;
                    if(document.querySelector('main')?.dataset.gameStatus==='finished')
                        return {finished:true,rolls,upgrades,cards,sawEvent};
                    if(click('使用奖励卡'))cards++;
                    else if(click('使用步数卡'))cards++;
                    else if(click('升级 地产'))upgrades++;
                    else if(click('掷骰前进'))rolls++;
                    else if(click('购买地产')){}
                    else if(click('放弃购买')){}
                    else click('结束当前回合');
                    await wait();
                }
                return {finished:false,rolls,upgrades,cards,sawEvent};
            }""")
            assert report['finished'] and report['rolls']>0,report
            assert not errors,errors
            print('PASS: P2 真浏览器文件导出→删除→导入→离线读档→完整对局',report)
            browser.close()
    finally:
        server.shutdown()
        thread.join()
if __name__=='__main__':main()
